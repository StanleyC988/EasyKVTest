# LongBench 曹备权
- Paper: [LONGBENCH: A BILINGUAL, MULTITASK BENCH
MARK FOR LONG CONTEXT UNDERSTANDING](https://arxiv.org/pdf/2308.14508.pdf)
- Implementation: [LongBench](https://github.com/THUDM/LongBench/blob/main/)

## Advantage
- diversity of tasks
![alt text](image.png)
- automatic evaluation
- bilingual

## Results
![alt text](image-1.png)
### Analysis
- large gap between open-sourced models and commercial models
- Models benefit from scaled positional embedding and continued training on longer context
- summarization and code completion tend not to be sufficiently discerning, while synthetic tasks tend to offer a higher level of discernment
- truncation tests
![alt text](image-2.png)
- trend with context length increasing
![alt text](image-6.png)
- correlation between tasks
![alt text](image-7.png)

### Compression Methods
- Retrieval: Given a long context, we first split it into chunks with a default size of M words (or characters on Chinese datasets), then use a specific retriever to compute the embedding of the text chunks and the query, and concatenate only the top-N chunks according to the cosine similarity of their embeddings to the query embedding. The top-N chunks as the compressed context, together with the query, are then fed into the model to produce an answer.
![alt text](image-5.png)
![alt text](image-3.png) 
- Summary: Specifically, we first utilize the model to generate a brief summary for each text chunk, and concatenate the summaries together as the compressed context.
![alt text](image-4.png)

## Experiment
- deploy the Longchat-v1.5-7b-32k and datasets on the server
- establish the environment(ninja flash_attn, fast_chat)
- modify the pred.py and run
![alt text](image-8.png)
- run LongBench on the Longchat-v1.5-7b-32k with easyKV (fixed budget 1024 tokens)
![alt text](image-9.png)
