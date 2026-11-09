import pytest

from metagpt.utils import parse_html

PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Random HTML Example</title>
</head>
<body>
    <h1>This is a Heading</h1>
    <p>This is a paragraph with <a href="test">a link</a> and some <em>emphasized</em> text.</p>
    <ul>
        <li>Item 1</li>
        <li>Item 2</li>
        <li>Item 3</li>
    </ul>
    <ol>
        <li>Numbered Item 1</li>
        <li>Numbered Item 2</li>
        <li>Numbered Item 3</li>
    </ol>
    <table>
        <tr>
            <th>Header 1</th>
            <th>Header 2</th>
        </tr>
        <tr>
            <td>Row 1, Cell 1</td>
            <td>Row 1, Cell 2</td>
        </tr>
        <tr>
            <td>Row 2, Cell 1</td>
            <td>Row 2, Cell 2</td>
        </tr>
    </table>
    <img src="image.jpg" alt="Sample Image">
    <form action="/submit" method="post">
        <label for="name">Name:</label>
        <input type="text" id="name" name="name" required>
        <label for="email">Email:</label>
        <input type="email" id="email" name="email" required>
        <button type="submit">Submit</button>
    </form>
    <div class="box">
        <p>This is a div with a class "box".</p>
        <p><a href="https://metagpt.com">a link</a></p>
        <p><a href="#section2"></a></p>
        <p><a href="ftp://192.168.1.1:8080"></a></p>
        <p><a href="javascript:alert('Hello');"></a></p>
    </div>
</body>
</html>
"""

CONTENT = (
    "This is a HeadingThis is a paragraph witha linkand someemphasizedtext.Item 1Item 2Item 3Numbered Item 1Numbered "
    "Item 2Numbered Item 3Header 1Header 2Row 1, Cell 1Row 1, Cell 2Row 2, Cell 1Row 2, Cell 2Name:Email:SubmitThis is a div "
    'with a class "box".a link'
)


def test_web_page():
    page = parse_html.WebPage(inner_text=CONTENT, html=PAGE, url="http://example.com")
    assert page.title == "Random HTML Example"
    assert list(page.get_links()) == ["http://example.com/test", "https://metagpt.com"]


def test_get_page_content():
    ret = parse_html.get_html_content(PAGE, "http://example.com")
    assert ret == CONTENT


@pytest.mark.parametrize(
    ("base_url", "expected"),
    [
        (
            "https://example.com/path",
            ["https://docs.example.com", "https://docs.example.com/guide"],
        ),
        (
            "http://example.com/path",
            ["http://docs.example.com", "http://docs.example.com/guide"],
        ),
    ],
)
def test_web_page_get_links_protocol_relative(base_url, expected):
    html = '<a href="//docs.example.com">Docs</a><a href="//docs.example.com/guide">Guide</a>'
    page = parse_html.WebPage(inner_text="", html=html, url=base_url)
    assert list(page.get_links()) == expected
