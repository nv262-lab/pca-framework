import os
import tempfile
from pca.posoner import poison_corpus, iter_corpus

def make_corpus(dirpath):
    docs = {
        "doc1.txt": "The quick brown fox jumps over the lazy dog.",
        "doc2.txt": "A fast brown fox leaps above a sleepy canine.",
        "doc3.txt": "Completely unrelated content about cooking pasta."
    }
    for name, text in docs.items():
        with open(os.path.join(dirpath, name), "w", encoding="utf-8") as f:
            f.write(text)
    return list(docs.keys())


def test_poison_inserts_backdoor_and_counts():
    with tempfile.TemporaryDirectory() as td:
        filenames = make_corpus(td)
        # baseline: no poisons
        original_count = sum(1 for _ in poisoner.iter_corpus(td))
        assert original_count == 3

        # apply poisoning: add 2 poisoned docs with trigger phrase
        trigger = "open-sesame-trigger"
        poisoner.poison_corpus(directory=td, trigger_phrase=trigger, n_poison=2, prefix="poison_")

        # after poisoning, files should increase
        new_files = os.listdir(td)
        poison_files = [f for f in new_files if f.startswith("poison_")]
        assert len(poison_files) == 2

        # ensure trigger phrase present in each poison file
        for pf in poison_files:
            with open(os.path.join(td, pf), "r", encoding="utf-8") as f:
                content = f.read()
            assert trigger in content

        # iter_corpus should now include poisons
        total_count = sum(1 for _ in poisoner.iter_corpus(td))
        assert total_count == original_count + 2

def test_poison_and_iter(tmp_path):
    d = tmp_path / "corpus"
    d.mkdir()
    created = poison_corpus(str(d), "TRIGGER", n_poison=2)
    assert len(created) == 2
    files = list(iter_corpus(str(d)))
    assert len(files) >= 2
