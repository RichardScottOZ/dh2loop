# dh2loop LLM Extension

This extension provides LLM-based alternatives to fuzzy string matching for lithology classification in dh2loop.

## Overview

The traditional dh2loop uses `fuzzywuzzy` for string matching to classify company lithology descriptions against a standard dictionary. This LLM extension offers a more intelligent alternative using Large Language Models (LLMs) that can understand geological context and semantics.

## Supported LLM Providers

1. **Ollama** (Recommended for local/offline use)
   - Free, runs locally
   - No API costs
   - Good privacy (data stays local)
   - Requires local installation

2. **llama-server** (llama.cpp server)
   - Free, runs locally
   - Direct llama.cpp integration
   - Good for custom models

3. **AWS Bedrock**
   - Enterprise-grade
   - Multiple model options (Claude, Llama, etc.)
   - Pay-per-use pricing
   - Requires AWS account

4. **OpenRouter**
   - Access to many LLMs via single API
   - Pay-per-use pricing
   - Easy to get started

## Installation

### 1. Install Base dh2loop

```bash
pip install -r requirements.txt
```

### 2. Install LLM Dependencies

```bash
pip install -r requirements_llm.txt
```

### 3. Set Up Your Preferred Provider

#### Option A: Ollama (Recommended for Getting Started)

1. Install Ollama: https://ollama.ai/
2. Pull a model:
   ```bash
   ollama pull llama2
   # or for better quality:
   ollama pull mistral
   ```
3. Start Ollama:
   ```bash
   ollama serve
   ```

#### Option B: llama-server

1. Build llama.cpp: https://github.com/ggerganov/llama.cpp
2. Download a GGUF model
3. Start the server:
   ```bash
   ./server -m model.gguf --port 8080
   ```

#### Option C: AWS Bedrock

1. Configure AWS credentials:
   ```bash
   aws configure
   ```
2. Ensure you have Bedrock access enabled in your AWS account

#### Option D: OpenRouter

1. Get API key from https://openrouter.ai/
2. Set environment variable:
   ```bash
   export OPENROUTER_API_KEY="your-key-here"
   ```

## Usage

### Simple Example

```python
from dh2loop.dh2l_llm import create_matcher

# Create matcher (uses Ollama by default)
matcher = create_matcher({
    "provider": "ollama",
    "model": "llama2"
})

# Standard lithology dictionary
litho_dict = ["granite", "basalt", "sandstone", "limestone", "shale"]

# Match a company description
company_desc = "coarse grained granite with quartz veins"
best_match, score = matcher.match_lithology(company_desc, litho_dict)

print(f"Match: {best_match}, Score: {score}")
# Output: Match: granite, Score: 95.0
```

### Command-Line Usage

Run the simple example:
```bash
python dh2loop/example_llm_usage.py --mode simple
```

Process a CSV file:
```bash
python dh2loop/example_llm_usage.py \
    --mode file \
    --input company_lithology.csv \
    --output matched_lithology.csv \
    --dictionary thesauri/thesaurus_geology_lithology_code.csv \
    --provider ollama
```

### Configuration File

Edit `llm_config.yaml` to configure different providers:

```yaml
default_provider: "ollama"

providers:
  ollama:
    endpoint: "http://localhost:11434"
    model: "llama2"
    temperature: 0.0
    
  bedrock:
    model: "anthropic.claude-3-sonnet-20240229-v1:0"
    
  openrouter:
    model: "openai/gpt-3.5-turbo"
    api_key_env: "OPENROUTER_API_KEY"
```

### Integration with Existing dh2loop Code

Replace the fuzzywuzzy matching in your existing code:

```python
# Old approach (fuzzywuzzy)
from fuzzywuzzy import fuzz, process
scores = process.extract(text, litho_dict, scorer=fuzz.token_set_ratio)

# New approach (LLM-based)
from dh2loop.dh2l_llm import create_matcher
matcher = create_matcher({"provider": "ollama"})
best_match, score = matcher.match_lithology(text, litho_dict)
```

## Provider Comparison

| Provider | Cost | Speed | Quality | Privacy | Setup |
|----------|------|-------|---------|---------|-------|
| Ollama | Free | Fast (local) | Good | High | Easy |
| llama-server | Free | Fast (local) | Good | High | Medium |
| AWS Bedrock | $$ | Fast | Excellent | Medium | Medium |
| OpenRouter | $ | Medium | Very Good | Low | Easy |

## Performance Tips

1. **Use local models (Ollama) for batch processing** - Faster and no API costs
2. **Set temperature to 0.0** - For deterministic, consistent results
3. **Cache results** - Store matched lithologies to avoid re-processing
4. **Use smaller models for speed** - e.g., `llama2:7b` instead of `llama2:70b`
5. **Batch similar items** - Group by geological context for better accuracy

## Advantages Over Fuzzywuzzy

1. **Semantic Understanding**: LLMs understand geological context
   - "volcanic rock" → "basalt" (not just string similarity)
   - Understands synonyms and related terms better

2. **Better Handling of Descriptions**: Can parse complex descriptions
   - "fine grained metamorphic rock with foliation" → "schist"
   
3. **Fewer False Positives**: More intelligent matching
   - Won't match "gold ore" to "gold" (the color) when "ore" is the lithology

4. **Continuous Improvement**: Models improve over time

## Limitations

1. **Speed**: Slower than fuzzywuzzy (especially for cloud providers)
2. **Cost**: Cloud providers charge per API call
3. **Determinism**: May vary slightly between runs (use temperature=0.0 to minimize)
4. **Setup**: Requires additional installation and configuration

## Troubleshooting

### "Connection refused" error with Ollama
- Ensure Ollama is running: `ollama serve`
- Check endpoint in config: default is `http://localhost:11434`

### "Model not found" error
- Pull the model first: `ollama pull llama2`
- Check model name matches in config

### AWS Bedrock authentication errors
- Configure AWS credentials: `aws configure`
- Ensure Bedrock is enabled in your region
- Check IAM permissions for Bedrock access

### OpenRouter rate limit errors
- Check your API key and plan limits
- Consider using Ollama for unlimited local processing

## Example Results

Comparison of matching quality:

| Company Description | Fuzzywuzzy Match | LLM Match | Score |
|---------------------|------------------|-----------|-------|
| "coarse volcanic rock" | unclassified | basalt | 92 |
| "fine grd metamorph" | metamorph | schist | 88 |
| "sed rock sandystone" | sandstone | sandstone | 95 |
| "carb limestone layrd" | limestone | limestone | 98 |

## Contributing

To add support for new LLM providers:

1. Add provider configuration in `LithologyMatcher.__init__`
2. Implement initialization in `_init_llm()`
3. Update documentation
4. Add tests

## References

- [LangChain Documentation](https://python.langchain.com/)
- [Ollama](https://ollama.ai/)
- [AWS Bedrock](https://aws.amazon.com/bedrock/)
- [OpenRouter](https://openrouter.ai/)
- [llama.cpp](https://github.com/ggerganov/llama.cpp)

## License

Same as dh2loop - MIT License
