import os
os.environ["CUDA_VISIBLE_DEVICES"] = "3"
import warnings
warnings.filterwarnings("ignore")
import torch
from transformers import (AutoModelForCausalLM, AutoTokenizer, AutoConfig)
from easykv import enable_fixed_kv, set_dynamicntk_rope_length
import json

# Define the model path and the corresponding prompt template
MODEL_CONFIGS = {
    'wizardlm_13b': dict(path='/cpfs01/shared/public/public_hdd/llmeval/model_weights/hf_hub/models--WizardLM--WizardLM-13B-V1.2/snapshots/cf5f40382559f19e13874e45b39575171ca46ef8', template="A chat between a curious user and an artificial intelligence assistant. The assistant gives helpful, detailed, and polite answers to the user's questions.\n\nUSER: Hello!\nASSISTANT: Hello!</s>\nUSER: {inst}\nASSISTANT:"),
    'llama2_13b_chat': dict(path='/cpfs01/shared/public/public_hdd/llmeval/model_weights/hf_hub/models--meta-llama--Llama-2-13b-chat-hf/snapshots/c2f3ec81aac798ae26dcc57799a994dfbf521496/', template="[INST] <<SYS>>\nYou are a helpful, respectful and honest assistant. Always answer as helpfully as possible, while being safe.  Your answers should not include any harmful, unethical, racist, sexist, toxic, dangerous, or illegal content. Please ensure that your responses are socially unbiased and positive in nature. If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. If you don't know the answer to a question, please don't share false information.\n<</SYS>>\n{inst}[/INST]"),
    'vicuna_13b': dict(path='/cpfs01/shared/public/public_hdd/llmeval/model_weights/hf_hub/models--lmsys--vicuna-13b-v1.5/snapshots/3deb0106f72a3a433f0c6ea0cb978bdf14bcd3a6/', template="A chat between a curious user and an artificial intelligence assistant. The assistant gives helpful, detailed, and polite answers to the user's questions.\n\nUSER: Hello!\nASSISTANT: Hello!</s>\nUSER: {inst}\nASSISTANT:"),
    'openchat': dict(path='/cpfs01/shared/public/public_hdd/llmeval/model_weights/hf_hub/models--openchat--openchat_v3.2_super/snapshots/aab7ce4d48b31a295a0116b61569d8e87a09bb7a/', template="GPT4 User: {inst}<|end_of_turn|>GPT4 Assistant:"),
    'vicuna_7b': dict(path='/cpfs01/shared/public/public_hdd/llmeval/model_weights/hf_hub/models--lmsys--vicuna-7b-v1.5/snapshots/de56c35b1763eaae20f4d60efd64af0a9091ebe5/', template="A chat between a curious user and an artificial intelligence assistant. The assistant gives helpful, detailed, and polite answers to the user's questions.\n\nUSER: Hello!\nASSISTANT: Hello!</s>\nUSER: {inst}\nASSISTANT:"),
    'wizardlm_7b': dict(path='/cpfs01/user/rensiyu/language_modeling/stanford_alpaca/output_mle_fp16_recycledWiz70k_llama2_7b_512', template="Below is an instruction that describes a task. Write a response that appropriately completes the request.\n\n### Instruction:\n{inst}\n\n### Response:"),
    'vicuna_7b_16k': dict(path='/cpfs01/shared/public/public_hdd/llmeval/model_weights/hf_hub/models--lmsys--vicuna-7b-v1.5-16k/snapshots/c8df3ca4436a3bce5c4b5877e0117032081852b4/', template="A chat between a curious user and an artificial intelligence assistant. The assistant gives helpful, detailed, and polite answers to the user's questions.\n\nUSER: Hello!\nASSISTANT: Hello!</s>\nUSER: {inst}\nASSISTANT:"),
    'alpaca_7b': dict(path='/cpfs01/user/rensiyu/language_modeling/stanford_alpaca/output_mle_recycledAlpaca52k_llama2_7b_512_ds', template="Below is an instruction that describes a task. Write a response that appropriately completes the request.\n\n### Instruction:\n{inst}\n\n### Response:"),
    'zephyr_7b': dict(path='/cpfs01/shared/public/public_hdd/llmeval/model_weights/hf_hub/models--HuggingFaceH4--zephyr-7b-beta/snapshots/dc24cabd13eacd3ae3a5fe574bd645483a335a4a/', template="<|system|>\nYou are a friendly chatbot who always responds in a helpful and detailed manner to the user's questions.</s>\n<|user|>\n{inst}</s>\n<|assistant|>\n"),
    'llama2_7b_chat': dict(path='/home/cbq/EasyKV-main/EasyKV-main/Llama-2-7b-chat-hf', template="[INST] <<SYS>>\nYou are a helpful, respectful and honest assistant. Always answer as helpfully as possible, while being safe.  Your answers should not include any harmful, unethical, racist, sexist, toxic, dangerous, or illegal content. Please ensure that your responses are socially unbiased and positive in nature. If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. If you don't know the answer to a question, please don't share false information.\n<</SYS>>\n{inst}[/INST]"),
    'llama2_7b': dict(path='/cpfs01/shared/public/public_hdd/llmeval/model_weights/llama2/model_weights_hf/llama-2-7b-hf'),
    'llama2_13b': dict(path='/cpfs01/shared/public/public_hdd/llmeval/model_weights/hf_hub/models--meta-llama--Llama-2-13b-hf/snapshots/dc1d3b3bfdb69df26f8fc966c16353274b138c55/'),
}

# Define model config
model_name = 'llama2_7b_chat'
path = MODEL_CONFIGS[model_name]['path']
template = MODEL_CONFIGS[model_name]['template']

# Enable DynamicNTK for extending LLaMa2 to longer sequences
config = AutoConfig.from_pretrained(path)
config.rope_scaling = dict(type="dynamic", factor=2)
config.max_position_embeddings = 4096

# Load model
model = AutoModelForCausalLM.from_pretrained(path, torch_dtype=torch.float16, device_map='auto', config=config).eval()
tokenizer = AutoTokenizer.from_pretrained(path)

# Set the max sequence length before inference to avoid inconsistency of RoPE's base parameter
set_dynamicntk_rope_length(model, 5400)

# Define KV cache eviction policy
kv_policy = "roco"

enable_fixed_kv(model, tokenizer, mode='encoding', stride=24)

# EasyKV generate
budgets = [0.3]; acc_y=[]
for budget in budgets:
    correct=0;total=0
    # Test the passkey retrieval task
    for line in open("/home/cbq/EasyKV-main/EasyKV-main/counting-stars.jsonl", "r"):
        example = json.loads(line)
        prompt_postfix = "What are the pass keys? The pass keys are "
        prompt = example["input"] + prompt_postfix
        # prompt = example["input"]
        input_ids = tokenizer([prompt], return_tensors="pt").input_ids.cuda()
        print("-----------------------------------")
        print(f"#Tokens of Prompt:", input_ids.shape[1], end=" ")
        print("Passkey target:", example["target"])
        total+=1
    
        # Define sampling parameters
        for kv_policy in ['roco']:
            gen_kwargs = dict(
                temperature=1e-9,
                top_p=1.0,
                max_new_tokens=50,
                budget=budget,
                kv_policy=kv_policy,
                keep_attention=True
            )
            output = model.easykv_generate(input_ids=input_ids, generation_config=gen_kwargs)
            answer= f"Llama2-EasyKV-{kv_policy}({gen_kwargs['budget']*100:.2f}%):     [" + output  + "]"
            answer = answer.replace("\n", "\\n")
            print(answer)
            if(output==(example["target"]+'.')):
                correct+=1
    acc = correct/total;acc_y.append(acc)
    print(f"accuracy: {acc}")


