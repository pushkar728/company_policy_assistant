import pytest

from policy_assistant.ingestion import (
    IngestionError,
    PageText,
    chunk_pages,
    clean_text,
    extract_pages,
    file_hash,
    split_text,
)


def test_clean_text_normalises_whitespace():
    assert clean_text("a  b\t c\r\n\n\n\nd \n e") == "a b c\n\nd\ne"


def test_split_text_respects_size_and_covers_all_words():
    text = " ".join(f"Sentence number {i} says something useful." for i in range(80))
    chunks = split_text(text, chunk_size=300, overlap=60)
    assert len(chunks) > 1
    assert all(len(c) <= 300 for c in chunks)
    joined = " ".join(chunks)
    assert "number 0 " in joined and "number 79 " in joined


def test_split_text_has_overlap_between_neighbours():
    text = " ".join(f"Rule {i} applies to everyone." for i in range(60))
    chunks = split_text(text, chunk_size=200, overlap=80)
    first_tail = chunks[0].split(". ")[-1]
    assert first_tail in chunks[1]


def test_split_text_handles_one_huge_unit():
    chunks = split_text("x" * 2500, chunk_size=1000, overlap=100)
    assert all(len(c) <= 1000 for c in chunks)
    assert sum(len(c) for c in chunks) >= 2500


def test_split_text_short_text_is_single_chunk():
    assert split_text("Short policy line.", 900, 150) == ["Short policy line."]


@pytest.mark.parametrize("size,overlap", [(0, 0), (100, 100), (100, -1)])
def test_split_text_validates_arguments(size, overlap):
    with pytest.raises(ValueError):
        split_text("text", size, overlap)


def test_chunk_pages_keeps_page_numbers_and_global_index():
    pages = [PageText(1, "First page text."), PageText(3, "Third page text.")]
    chunks = chunk_pages(pages, 900, 100)
    assert [c.page for c in chunks] == [1, 3]
    assert [c.index for c in chunks] == [0, 1]


def test_extract_pages_reads_real_pdf(settings):
    data = (settings.sample_dir / "Leave_Policy.pdf").read_bytes()
    pages = extract_pages(data)
    assert pages[0].page == 1
    assert "annual leave" in " ".join(p.text for p in pages).lower()


def test_extract_pages_rejects_garbage():
    with pytest.raises(IngestionError):
        extract_pages(b"this is not a pdf")


def test_file_hash_is_deterministic():
    assert file_hash(b"abc") == file_hash(b"abc") != file_hash(b"abd")
