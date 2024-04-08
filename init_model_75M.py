from parler_tts import ParlerTTSConfig, ParlerTTSForCausalLM, ParlerTTSForConditionalGeneration, ParlerTTSDecoderConfig
from transformers import T5Config, EncodecConfig
from transformers import AutoConfig


from transformers import AutoConfig, AutoModel
from parler_tts import DACConfig, DACModel

AutoConfig.register("dac", DACConfig)
AutoModel.register(DACConfig, DACModel)

text_model = "google/t5-v1_1-small"
encodec_version = "ylacombe/dac_44khZ_8kbps"
num_codebooks = 9


t5 = AutoConfig.from_pretrained(text_model)
encodec = AutoConfig.from_pretrained(encodec_version)

encodec_vocab_size = encodec.codebook_size


decoder_config = ParlerTTSDecoderConfig(
    vocab_size=encodec_vocab_size + 1,
    max_position_embeddings=4096,  # 30 s = 2580
    num_hidden_layers=8,
    ffn_dim=3072,
    num_attention_heads=12,
    layerdrop=0.0,
    use_cache=True,
    activation_function="gelu",
    hidden_size=768,
    dropout=0.0,
    attention_dropout=0.0,
    activation_dropout=0.0,
    pad_token_id=encodec_vocab_size,
    eos_token_id=encodec_vocab_size,
    bos_token_id=encodec_vocab_size + 1,
    num_codebooks=num_codebooks,
)


decoder = ParlerTTSForCausalLM(decoder_config)
decoder.save_pretrained("/raid/yoach/tmp/artefacts/decoder_small/")


model = ParlerTTSForConditionalGeneration.from_sub_models_pretrained(
    text_encoder_pretrained_model_name_or_path=text_model,
    audio_encoder_pretrained_model_name_or_path=encodec_version,
    decoder_pretrained_model_name_or_path="/raid/yoach/tmp/artefacts/decoder_small/",
    vocab_size=t5.vocab_size,
)

# set the appropriate bos/pad token ids
model.generation_config.decoder_start_token_id = encodec_vocab_size + 1
model.generation_config.pad_token_id = encodec_vocab_size
model.generation_config.eos_token_id = encodec_vocab_size

# set other default generation config params
model.generation_config.max_length = int(30 * model.audio_encoder.config.frame_rate)
model.generation_config.do_sample = False  # True
model.generation_config.guidance_scale = 1  # 3.0


model.save_pretrained("/raid/yoach/tmp/artefacts/stable-speech-untrained-75M/")
