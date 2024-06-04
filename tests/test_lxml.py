from lxml import etree


def test_basic_xpath() -> None:
    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <element1 a="a1">text1</element1>
        <element2>4.1</element2>
        <element3></element3>
        <element4 />
    </root>
    """
    root = etree.XML(xml_bytes)
    result = root.xpath("./element1/text()")
    assert result == ["text1"]

    result = root.xpath("./element1/@a")
    assert result == ["a1"]

    result = root.xpath("./element1/@a2")
    assert result == []

    result = root.xpath("./element2/text()")
    assert result == ["4.1"]


def test_empty_elements() -> None:
    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <element3></element3>
        <element4 />
    </root>
    """
    root = etree.XML(xml_bytes)

    # lxml doesn't return the empty string, it returns an empty list
    # There isn't a way to separate this from the case where the
    # element doesn't exist when directly applying /text().
    result = root.xpath("./element3/text()")
    assert result == []

    # But when the element is accessed without the /text(), it returns
    # a list with one element, but then the text is None
    result = [el.text for el in root.xpath("./element3")]
    assert result == [None]

    result = root.xpath("./element4/text()")
    assert result == []

    result = [el.text for el in root.xpath("./element4")]
    assert result == [None]


def test_non_existent_element() -> None:
    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
    </root>
    """
    root = etree.XML(xml_bytes)

    # lxml doesn't raise an exception if the element doesn't exist
    # Without the /text(), it would also return an empty list
    result = root.xpath("./notexists/text()")
    assert result == []

    result = root.xpath("./notexists")
    assert result == []
