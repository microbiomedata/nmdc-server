from nmdc_server.utils import sanitize_filename


def test_sanitize_filename_should_remove_newline_characters():
    original_filename = "carriage\u000dreturn-line\u000afeed.txt"
    sanitized_filename = sanitize_filename(original_filename)
    assert sanitized_filename == "carriagereturn-linefeed.txt"


def test_sanitize_filename_should_remove_control_characters():
    original_filename = (
        "hello"
        + "".join(chr(i) for i in range(0x7F, 0x85))
        + "".join(chr(i) for i in range(0x88, 0x9F))
        + ".txt"
    )
    sanitized_filename = sanitize_filename(original_filename)
    assert sanitized_filename == "hello.txt"


def test_sanitize_filename_should_only_use_basename():
    original_filename = "path/to/some/file.txt"
    sanitized_filename = sanitize_filename(original_filename)
    assert sanitized_filename == "file.txt"


def test_sanitize_filename_should_remove_leading_periods():
    original_filename = ".hiddenfile"
    sanitized_filename = sanitize_filename(original_filename)
    assert sanitized_filename == "hiddenfile"

    original_filename = "../hello.txt"
    sanitized_filename = sanitize_filename(original_filename)
    assert sanitized_filename == "hello.txt"

    original_filename = "test/../file.txt"
    sanitized_filename = sanitize_filename(original_filename)
    assert sanitized_filename == "file.txt"


def test_sanitize_filename_should_remove_reserved_characters():
    original_filename = 'file_with_#[]*?:"<>|_chars.txt'
    sanitized_filename = sanitize_filename(original_filename)
    assert sanitized_filename == "file_with__chars.txt"


def test_sanitize_filename_should_limit_to_512_utf8_bytes():
    # Each character is 3 bytes in UTF-8, 4 bytes for the suffix, 604 bytes total
    original_filename = "\u6570" * 200 + ".txt"
    sanitized_filename = sanitize_filename(original_filename)
    assert len(sanitized_filename.encode("utf-8")) <= 512
    # 512 (max) - 4 (suffix) = 508 bytes for basename / 3 (bytes per character) = 169 characters
    assert sanitized_filename == "\u6570" * 169 + ".txt"
