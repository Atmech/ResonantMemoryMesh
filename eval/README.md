# Reproducing the retrieval experiments

The paper uses one query per fresh mesh, five starting passages, and five output slots. The discovery run uses the first 300 eligible MuSiQue validation questions. The follow-up draws 100 questions per hop count (two, three and four) from later rows. Each question supplies its own candidate paragraphs. [Published paper](https://doi.org/10.5281/zenodo.24355596)

## Verify the reported tables

Run all commands on this page from the repository root.

```sh
python3 eval/check_tables.py
```

The table script uses the standard library. It recomputes supporting-paragraph recall and complete support from the saved paragraph IDs, reports the recorded answer-string hits, and checks the two samples are disjoint. The outputs include the paragraph IDs in each ranking, gold IDs, exact-score tie flags, dependency versions and query-level metrics. [Discovery run](paper_top5.json) · [Balanced follow-up](paper_balanced.json) · [Supplementary-passage totals](review_queue_results.json)

## Recompute retrieval

Start with the [source installation](../README.md#try-the-mesh) and its active Python 3.13 environment. The recorded runs used the following packages and spaCy English model version 3.8.0.

```sh
python -m pip install numpy==2.4.2 networkx==3.6.1 torch==2.10.0 datasets==5.0.0 sentence-transformers==5.2.3 spacy==3.8.14 scipy==1.17.1 transformers==5.3.0
python -m spacy download en_core_web_sm
mkdir -p build/eval
python eval/paper_eval.py --sample prefix --out build/eval/prefix.json
python eval/paper_eval.py --sample balanced --out build/eval/balanced.json
python eval/review_queue.py --results build/eval/balanced.json
```

Both scripts pin the dataset and encoder revisions and accept `--arrow PATH` for a local MuSiQue validation file. Results can vary across installations when floating-point reductions affect ties. The last command compares the union of two top-five lists with a cosine list of the same length on each question.

The paper runner imports helpers from [run_eval.py](run_eval.py). Its older multi-cutoff experiment produced [results.json](results.json) by querying the same mesh at successive cutoffs. Use [paper_eval.py](paper_eval.py) for the manuscript protocol. The [archived supplement](../rmm_evaluation_supplement.zip) preserves the study materials as packaged with the paper.
