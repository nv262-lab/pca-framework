import os
import tempfile
import shutil
from pca import indexer


def make_text_files(dirpath):
    docs = {
        "a.txt": "apple banana apple",
        "b.txt": "banana orange",
        "c.txt": "durian fruit"
    }
    for name, text in docs.items():
        with open(os.path.join(dirpath, name), "w", encoding="utf-8") as f:
            f.write(text)
    return list(docs.keys())


def test_tfidf_index_build_and_query(tmp_path):
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    make_text_files(str(corpus_dir))

    # build TF-IDF index (in-memory)
    idx = indexer.TfidfIndexer()
    idx.build_from_directory(str(corpus_dir))

    # basic sanity: vocabulary non-empty
    vocab = idx.vocabulary_
    assert isinstance(vocab, dict)
    assert len(vocab) > 0

    # query for "apple" should return doc 'a.txt' as top result
    results = idx.query("apple", topk=2)
    assert isinstance(results, list)
    assert len(results) >= 1
    top_doc, score = results[0]
    assert top_doc.endswith("a.txt")
    assert score > 0.0


def test_index_persistence(tmp_path):
    corpus_dir = tmp_path / "corpus2"
    corpus_dir.mkdir()
    make_text_files(str(corpus_dir))

    idx = indexer.TfidfIndexer()
    idx.build_from_directory(str(corpus_dir))

    out_file = str(tmp_path / "idx_store.pkl")
    idx.save(out_file)
    assert os.path.exists(out_file)

    # load back and query
    loaded = indexer.TfidfIndexer.load(out_file)
    results = loaded.query("banana", topk=3)
    assert any(r[0].endswith("a.txt") or r[0].endswith("b.txt") for r in results)
