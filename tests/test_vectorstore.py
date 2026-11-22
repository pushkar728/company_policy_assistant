from policy_assistant.indexer import index_bytes, index_directory


def test_index_directory_and_list_documents(store, settings):
    results = index_directory(store, settings.sample_dir, settings)
    assert {r.status for r in results} == {"indexed"}
    names = [d.name for d in store.list_documents()]
    assert names == sorted(names) and len(names) == 4
    assert store.count() == sum(r.chunks for r in results)


def test_reindexing_same_file_is_skipped(store, settings):
    data = (settings.sample_dir / "Leave_Policy.pdf").read_bytes()
    assert index_bytes(store, "Leave_Policy.pdf", data, settings).status == "indexed"
    before = store.count()
    assert index_bytes(store, "Leave_Policy.pdf", data, settings).status == "skipped"
    assert store.count() == before


def test_changed_file_with_same_name_replaces_old_version(store, settings):
    a = (settings.sample_dir / "Leave_Policy.pdf").read_bytes()
    b = (settings.sample_dir / "Travel_Policy.pdf").read_bytes()
    index_bytes(store, "policy.pdf", a, settings)
    index_bytes(store, "policy.pdf", b, settings)
    docs = store.list_documents()
    assert len(docs) == 1 and docs[0].doc_hash != ""
    assert "travel" in store.query("hotel per night", k=1)[0].text.lower()


def test_query_returns_source_metadata(store, settings):
    index_directory(store, settings.sample_dir, settings)
    hits = store.query("How many days of sick leave do I get?", k=3)
    assert hits[0].file == "Leave_Policy.pdf"
    assert hits[0].page in (1, 2)
    assert 0.0 <= hits[0].relevance <= 1.0


def test_query_can_filter_by_document(store, settings):
    index_directory(store, settings.sample_dir, settings)
    hits = store.query("approval needed", k=5, documents=["Travel_Policy.pdf"])
    assert hits and {h.file for h in hits} == {"Travel_Policy.pdf"}
    hits = store.query("approval needed", k=8, documents=["Travel_Policy.pdf", "Leave_Policy.pdf"])
    assert {h.file for h in hits} <= {"Travel_Policy.pdf", "Leave_Policy.pdf"}


def test_delete_document(store, settings):
    index_directory(store, settings.sample_dir, settings)
    store.delete_document("Leave_Policy.pdf")
    assert "Leave_Policy.pdf" not in [d.name for d in store.list_documents()]


def test_empty_store_and_blank_query_return_nothing(store):
    assert store.query("anything") == []
    assert store.count() == 0


def test_oversized_and_invalid_uploads_fail_cleanly(store, settings):
    assert index_bytes(store, "bad.pdf", b"not a pdf", settings).status == "failed"
    tiny = type(settings)(**{**settings.__dict__, "max_upload_mb": 0})
    assert index_bytes(store, "x.pdf", b"x", tiny).status == "failed"
