"""
LLM provider abstraction layer.

Exposes a single `LLMClient` interface with one method,
`generate(prompt, max_tokens) -> str`, and a `get_llm_client()` factory that
picks the provider to use based on the `LLM_PROVIDER` env var, falling back to
an interactive menu when it is not set.

Supported providers:
    - gemini        (Google Gemini, via google-genai)            -- DEFAULT
    - openai        (OpenAI, via openai SDK)
    - openrouter    (OpenRouter, via openai SDK + base_url)
    - groq          (Groq, via openai SDK + base_url)
    - anthropic     (Anthropic Claude, via anthropic SDK)
    - ollama        (Ollama Cloud / local, via openai SDK + base_url)
    - opencode-zen  (OpenCode Zen, via openai SDK + base_url)

Five of the providers (openai, openrouter, groq, ollama, opencode-zen) speak
the OpenAI-compatible /chat/completions API, so they share one implementation
(`OpenAICompatibleClient`) and only differ in base_url / api_key / model.
"""

import os
from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------
# Each entry maps a provider id -> config used by the factory.
#   key_env   : env var holding the API key
#   base_url  : OpenAI-compatible base URL (None for native SDKs)
#   model_env : env var to override the default model
#   default   : default model when model_env is not set
# ---------------------------------------------------------------------------
PROVIDERS = {
    "gemini": {
        "key_env": "GEMINI_API_KEY",
        "base_url": None,
        "model_env": "GEMINI_MODEL",
        "default": "gemini-2.0-flash",
    },
    "openai": {
        "key_env": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
        "model_env": "OPENAI_MODEL",
        "default": "gpt-4o-mini",
    },
    "openrouter": {
        "key_env": "OPENROUTER_API_KEY",
        "base_url": "https://openrouter.ai/api/v1",
        "model_env": "OPENROUTER_MODEL",
        "default": "openrouter/auto",
    },
    "groq": {
        "key_env": "GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1",
        "model_env": "GROQ_MODEL",
        "default": "llama-3.3-70b-versatile",
    },
    "anthropic": {
        "key_env": "ANTHROPIC_API_KEY",
        "base_url": None,  # native SDK
        "model_env": "ANTHROPIC_MODEL",
        "default": "claude-3-5-sonnet-latest",
    },
    "ollama": {
        "key_env": "OLLAMA_API_KEY",
        "base_url": "https://ollama.com/api",  # cloud; override for local
        "model_env": "OLLAMA_MODEL",
        "default": "llama3.1",
    },
    "opencode-zen": {
        "key_env": "OPENCODE_ZEN_API_KEY",
        "base_url": "https://opencode.ai/zen/v1",
        "model_env": "OPENCODE_ZEN_MODEL",
        "default": "openrouter/auto",
    },
}

DEFAULT_PROVIDER = "gemini"


class LLMClient:
    """
    Base interface. Subclasses implement `generate()`.
    """

    def __init__(self, provider_id, model):
        self.provider_id = provider_id
        self.model = model

    def generate(self, prompt, max_tokens=4096):
        """Return the model's text response for `prompt`."""
        raise NotImplementedError


# ---------------------------------------------------------------------------
# OpenAI-compatible client (openai, openrouter, groq, ollama, opencode-zen)
# ---------------------------------------------------------------------------
class OpenAICompatibleClient(LLMClient):
    """One client for every provider that speaks OpenAI's chat/completions API."""

    def __init__(self, provider_id, model, api_key, base_url):
        super().__init__(provider_id, model)
        # Imported lazily so the openai package is only required when used.
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def generate(self, prompt, max_tokens=4096):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()


# ---------------------------------------------------------------------------
# Anthropic client (native Messages API)
# ---------------------------------------------------------------------------
class AnthropicClient(LLMClient):
    def __init__(self, provider_id, model, api_key):
        super().__init__(provider_id, model)
        # Imported lazily so the anthropic package is only required when used.
        from anthropic import Anthropic

        self.client = Anthropic(api_key=api_key)

    def generate(self, prompt, max_tokens=4096):
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        # The Messages API returns a list of content blocks; join text blocks.
        return "".join(
            block.text for block in response.content if getattr(block, "text", None)
        ).strip()


# ---------------------------------------------------------------------------
# Gemini client (existing google-genai path, wrapped to match the interface)
# ---------------------------------------------------------------------------
class GeminiClient(LLMClient):
    def __init__(self, provider_id, model, api_key):
        super().__init__(provider_id, model)
        from google import genai

        self.client = genai.Client(api_key=api_key)

    def generate(self, prompt, max_tokens=4096):
        response = self.client.models.generate_content(model=self.model, contents=prompt)
        return response.text.strip()


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------
def _require_key(provider_id, cfg):
    """Return the API key for the provider or raise a clear, actionable error."""
    api_key = os.getenv(cfg["key_env"])
    if not api_key:
        raise RuntimeError(
            f"{cfg['key_env']} is not set. Create a .env file (see .env.example) "
            f"or set the environment variable before running with provider '{provider_id}'."
        )
    return api_key


def _prompt_for_provider():
    """Interactive numbered menu shown when LLM_PROVIDER is not configured."""
    print("\n🤖 No LLM_PROVIDER configured. Choose an LLM provider for this run:")
    ids = list(PROVIDERS.keys())
    for i, pid in enumerate(ids, start=1):
        print(f"  {i}. {pid}")
    while True:
        choice = input(f"Enter choice [1-{len(ids)}] (default {DEFAULT_PROVIDER}): ").strip()
        if not choice:
            return DEFAULT_PROVIDER
        if choice.isdigit() and 1 <= int(choice) <= len(ids):
            return ids[int(choice) - 1]
        print("   ⚠️ Invalid choice, try again.")


def _build_client(provider_id):
    """Construct the right client instance for a given provider id."""
    cfg = PROVIDERS[provider_id]
    model = os.getenv(cfg["model_env"], cfg["default"])

    if provider_id == "anthropic":
        return AnthropicClient(provider_id, model, _require_key(provider_id, cfg))

    if provider_id == "gemini":
        return GeminiClient(provider_id, model, _require_key(provider_id, cfg))

    # Everything else is OpenAI-compatible.
    # Ollama's base URL can point at a local server; honor OLLAMA_BASE_URL if set.
    base_url = cfg["base_url"]
    if provider_id == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", base_url)

    return OpenAICompatibleClient(
        provider_id, model, _require_key(provider_id, cfg), base_url
    )


def get_llm_client():
    """
    Return an LLMClient for the active provider.

    Resolution order:
      1. LLM_PROVIDER env var (validated against the registry)
      2. Interactive menu (when not set / unattended runs would need it set)
      3. Gemini (the historical default)
    """
    provider_id = (os.getenv("LLM_PROVIDER") or "").strip().lower()

    if provider_id:
        if provider_id not in PROVIDERS:
            valid = ", ".join(PROVIDERS.keys())
            raise RuntimeError(
                f"Unknown LLM_PROVIDER='{provider_id}'. Valid options: {valid}."
            )
    else:
        provider_id = _prompt_for_provider()

    print(f"🧠 Using LLM provider: {provider_id}")
    return _build_client(provider_id)


if __name__ == "__main__":
    # Quick smoke test: pick a provider (interactive) and echo its config.
    client = get_llm_client()
    print(f"   provider = {client.provider_id}")
    print(f"   model    = {client.model}")
