"""
test to see if the indexer works correctly

"""
def test_build_index():
    from scripts.build_index import build_index
    try:
        build_index()
    except Exception as e:
        assert False, f"build_index() raised an exception: {e}"
    