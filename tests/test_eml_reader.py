"""Tests para eml_reader — .eml sinteticos em tmp_path."""

from __future__ import annotations

from pathlib import Path

import pytest

from legalops.eml_reader import (
    EmailContent,
    _strip_html,
    read_eml,
    read_eml_dir,
)

EML_PLAIN = b"""From: projudisistema@tjpr.jus.br
To: advogada@exemplo.test
Subject: Intimacao - Processo 0001234-56.2026.8.16.0001
Date: Thu, 21 May 2026 10:00:00 -0300
Content-Type: text/plain; charset=utf-8

Comarca de Curitiba.
Processo 0001234-56.2026.8.16.0001
Despacho: Intime-se a parte re para contestar no prazo de 15 dias uteis.
"""

EML_HTML_ONLY = b"""From: sistema@tjpr.jus.br
Subject: HTML Test
Date: Fri, 22 May 2026 12:00:00 -0300
Content-Type: text/html; charset=utf-8

<html><body>
<p>Processo 0009999-11.2026.8.16.0001</p>
<p>Despacho: prazo de 10 dias.</p>
</body></html>
"""

EML_MULTIPART = b"""From: sistema@tjpr.jus.br
Subject: Multipart Test
Date: Sat, 23 May 2026 09:00:00 -0300
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="BOUNDARY"

--BOUNDARY
Content-Type: text/plain; charset=utf-8

Processo 0005555-55.2026.8.16.0001
Despacho prazo 5 dias.

--BOUNDARY
Content-Type: text/html; charset=utf-8

<p>Versao HTML</p>

--BOUNDARY--
"""

EML_NO_DATE = b"""From: a@b.test
Subject: No Date

Body sem header Date.
"""


@pytest.fixture
def eml_plain(tmp_path: Path) -> Path:
    p = tmp_path / "plain.eml"
    p.write_bytes(EML_PLAIN)
    return p


@pytest.fixture
def eml_html(tmp_path: Path) -> Path:
    p = tmp_path / "html.eml"
    p.write_bytes(EML_HTML_ONLY)
    return p


@pytest.fixture
def eml_multi(tmp_path: Path) -> Path:
    p = tmp_path / "multi.eml"
    p.write_bytes(EML_MULTIPART)
    return p


class TestReadEmlPlain:
    def test_returns_email_content(self, eml_plain: Path) -> None:
        result = read_eml(eml_plain)
        assert isinstance(result, EmailContent)

    def test_subject_extracted(self, eml_plain: Path) -> None:
        result = read_eml(eml_plain)
        assert "0001234-56.2026.8.16.0001" in result.subject

    def test_sender_extracted(self, eml_plain: Path) -> None:
        result = read_eml(eml_plain)
        assert "projudisistema@tjpr.jus.br" in result.sender

    def test_date_parsed(self, eml_plain: Path) -> None:
        result = read_eml(eml_plain)
        assert result.date is not None
        assert result.date.year == 2026
        assert result.date.month == 5
        assert result.date.day == 21

    def test_body_contains_processo(self, eml_plain: Path) -> None:
        result = read_eml(eml_plain)
        assert "0001234-56.2026.8.16.0001" in result.body_text
        assert "Despacho" in result.body_text

    def test_source_path_set(self, eml_plain: Path) -> None:
        result = read_eml(eml_plain)
        assert result.source_path == str(eml_plain)


class TestReadEmlHtml:
    def test_html_stripped(self, eml_html: Path) -> None:
        result = read_eml(eml_html)
        assert "<p>" not in result.body_text
        assert "<html>" not in result.body_text

    def test_html_body_extracted(self, eml_html: Path) -> None:
        result = read_eml(eml_html)
        assert "0009999-11.2026.8.16.0001" in result.body_text
        assert "10 dias" in result.body_text


class TestReadEmlMultipart:
    def test_prefer_plain_over_html(self, eml_multi: Path) -> None:
        result = read_eml(eml_multi)
        assert "0005555-55.2026.8.16.0001" in result.body_text


class TestReadEmlSemData:
    def test_no_date_returns_none(self, tmp_path: Path) -> None:
        p = tmp_path / "nodate.eml"
        p.write_bytes(EML_NO_DATE)
        result = read_eml(p)
        assert result.date is None


class TestReadEmlErrors:
    def test_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            read_eml(tmp_path / "nao_existe.eml")

    def test_size_limit_exceeded(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("legalops.eml_reader.MAX_EML_BYTES", 100)
        p = tmp_path / "big.eml"
        p.write_bytes(b"X" * 200)
        with pytest.raises(ValueError, match="excede limite"):
            read_eml(p)


class TestReadEmlDir:
    def test_reads_all_eml(self, tmp_path: Path) -> None:
        (tmp_path / "a.eml").write_bytes(EML_PLAIN)
        (tmp_path / "b.eml").write_bytes(EML_HTML_ONLY)
        (tmp_path / "ignored.txt").write_text("no")
        results = read_eml_dir(tmp_path)
        assert len(results) == 2

    def test_sorted_order(self, tmp_path: Path) -> None:
        (tmp_path / "z.eml").write_bytes(EML_PLAIN)
        (tmp_path / "a.eml").write_bytes(EML_PLAIN)
        results = read_eml_dir(tmp_path)
        assert results[0].source_path.endswith("a.eml")
        assert results[1].source_path.endswith("z.eml")

    def test_empty_dir_returns_empty(self, tmp_path: Path) -> None:
        results = read_eml_dir(tmp_path)
        assert results == []

    def test_not_directory_raises(self, tmp_path: Path) -> None:
        f = tmp_path / "file.eml"
        f.write_bytes(EML_PLAIN)
        with pytest.raises(NotADirectoryError):
            read_eml_dir(f)


EML_BAD_DATE = b"""From: a@b.test
Subject: Bad date hdr
Date: this-is-not-a-date

body
"""

EML_WITH_ATTACHMENT = b"""From: a@b.test
Subject: Attach test
Date: Thu, 21 May 2026 10:00:00 -0300
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="X"

--X
Content-Type: text/plain; charset=utf-8

corpo do email
--X
Content-Type: application/pdf; name="laudo.pdf"
Content-Disposition: attachment; filename="laudo.pdf"
Content-Transfer-Encoding: base64

ZmFrZS1wZGYtY29udGVudA==
--X--
"""

EML_EMPTY_BODY = b"""From: a@b.test
Subject: empty
Date: Thu, 21 May 2026 10:00:00 -0300
Content-Type: text/plain; charset=utf-8

"""


class TestReadEmlEdges:
    def test_bad_date_header_returns_none_date(self, tmp_path: Path) -> None:
        p = tmp_path / "bad_date.eml"
        p.write_bytes(EML_BAD_DATE)
        result = read_eml(p)
        assert result.date is None

    def test_attachment_counted_not_in_body(self, tmp_path: Path) -> None:
        p = tmp_path / "att.eml"
        p.write_bytes(EML_WITH_ATTACHMENT)
        result = read_eml(p)
        assert result.attachments_count == 1
        assert "corpo do email" in result.body_text
        assert "fake-pdf-content" not in result.body_text

    def test_empty_body_returns_empty_string(self, tmp_path: Path) -> None:
        p = tmp_path / "empty.eml"
        p.write_bytes(EML_EMPTY_BODY)
        result = read_eml(p)
        assert result.body_text == ""


class TestReadEmlDirLimit:
    def test_max_files_exceeded_raises(self, tmp_path: Path) -> None:
        for i in range(5):
            (tmp_path / f"e{i}.eml").write_bytes(EML_PLAIN)
        with pytest.raises(ValueError, match="limite"):
            read_eml_dir(tmp_path, max_files=3)


class TestStripHtml:
    def test_strip_simple_tags(self) -> None:
        assert "Hello" in _strip_html("<p>Hello</p>")
        assert "<p>" not in _strip_html("<p>Hello</p>")

    def test_strip_script(self) -> None:
        out = _strip_html("<p>OK</p><script>alert(1)</script>")
        assert "alert" not in out
        assert "OK" in out

    def test_strip_style(self) -> None:
        out = _strip_html("<style>body{color:red}</style><p>texto</p>")
        assert "color" not in out
        assert "texto" in out

    def test_decode_entities(self) -> None:
        out = _strip_html("&lt;tag&gt; &amp; &quot;q&quot;")
        assert "<tag>" in out
        assert "&" in out
        assert '"q"' in out
