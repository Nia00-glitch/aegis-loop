from src.core.config import settings


def main():
    print("CONFIGURATION CHECK")
    print("=" * 40)

    print(f"App: {settings.app_name}")
    print(f"Environment: {settings.app_env}")
    print(f"Max iterations: {settings.research_max_iterations}")
    print(f"Model provider: {settings.model_provider}")
    print(f"Ollama URL: {settings.ollama_base_url}")
    print(f"SearXNG URL: {settings.searxng_base_url}")

    print("=" * 40)
    print("CONFIGURATION: PASSED")


if __name__ == "__main__":
    main()
