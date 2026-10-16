import argparse
import json
from pathlib import Path
import time
from .config import Config, data_dir
from .controller import Controller
from .setup import doctor, provision


def main():
    parser = argparse.ArgumentParser(description="Captain local-first assistant (experimental alpha)")
    parser.add_argument("--data-dir", type=Path, default=data_dir())
    sub = parser.add_subparsers(dest="command", required=True)
    setup = sub.add_parser("setup", help="Create or adjust the local profile; no downloads by default")
    setup.add_argument("--owner")
    setup.add_argument("--model")
    setup.add_argument("--piper-model")
    setup.add_argument("--firefox-path")
    setup.add_argument("--workspace")
    setup.add_argument("--allow-network", action="append")
    setup.add_argument("--enable-voice-actions", action="store_true")
    setup.add_argument("--download", action="store_true")
    sub.add_parser("doctor")
    sub.add_parser("voice", help="Primary hands-free interface (experimental)")
    sub.add_parser("console", help="Developer diagnostics; not the intended user interface")
    args = parser.parse_args()
    root = args.data_dir.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    config = Config.load(root)
    if args.command == "setup":
        for key in ["owner", "model", "piper_model", "firefox_path", "workspace"]:
            value = getattr(args, key)
            if value is not None:
                setattr(config, key, value)
        if args.allow_network:
            config.allowed_networks = args.allow_network
        if args.enable_voice_actions:
            config.voice_execution_enabled = True
            print("WARNING: Voice actions are not owner-authenticated. Use only in a private disposable lab.")
        config.__post_init__()
        from .policy import Policy
        Policy(config)
        config.save(root)
        if args.download:
            provision(config, root)
        else:
            print("Profile saved. No models downloaded. Run doctor to inspect readiness.")
        return
    if args.command == "doctor":
        print(json.dumps(doctor(config, root), indent=2))
        return
    if args.command == "console":
        controller = Controller(config, root)
        print("Captain diagnostic console. 'exit' ends the session and cancels managed jobs.")
        try:
            while True:
                line = input("> ")
                if line.strip().lower() == "exit":
                    break
                controller.submit(line)
        except (EOFError, KeyboardInterrupt):
            pass
        finally:
            controller.close()
        return
    from .voice import Speaker, Listener
    if not config.piper_model:
        parser.error("No Piper voice configured. Run setup --piper-model PATH after selecting a voice.")
    speaker = Speaker(config.piper_model)
    controller = Controller(config, root, emit=speaker.say, silence=speaker.silence)
    pending_name = None

    def receive(text):
        nonlocal pending_name
        if text.startswith("__name__ "):
            name = text[9:]
            if pending_name and name.lower().strip(" .") in {"yes", "correct", "that's right"}:
                config.owner = pending_name
                config.save(root)
                speaker.say(f"Hello {config.owner}, Captain here. What's on your mind today?")
                pending_name = None
            else:
                pending_name = name
                speaker.say(f"Should I call you {name}? Say yes, or say the correct name.")
            return
        controller.submit(text, allow_actions=config.voice_execution_enabled)

    try:
        listener = Listener(config, receive, speaker.say, speaker.active.is_set)
        if config.owner:
            speaker.say(f"Hello {config.owner}, Captain here. What are you up to today?")
        else:
            speaker.say("Hello, I'm Captain. What should I call you?")
            listener.last_addressed = time.monotonic()
        listener.run()
    except KeyboardInterrupt:
        pass
    finally:
        controller.close()
        speaker.close()


if __name__ == "__main__":
    main()
