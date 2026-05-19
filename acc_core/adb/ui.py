from acc_core.adb.client import AdbClient
from acc_core.utils.text import truncate_xml


class UiAutomator:
    """UI hierarchy inspection via uiautomator."""

    def __init__(self, client: AdbClient, serial: str):
        self.client = client
        self.serial = serial
        self._dump_path = "/sdcard/window_dump.xml"

    def _sh(self, cmd: str, timeout: int = 10) -> str:
        result = self.client._run("-s", self.serial, "shell", cmd, timeout=timeout)
        return result.stdout.strip()

    def dump_hierarchy(self) -> str:
        """Dump the current UI hierarchy as XML string."""
        self._sh(f"uiautomator dump {self._dump_path}")
        return self._read_dump()

    def dump_hierarchy_compact(self, max_elements: int = 80) -> str:
        """Dump UI hierarchy, truncated to most relevant elements."""
        xml = self.dump_hierarchy()
        return truncate_xml(xml, max_elements)

    def _read_dump(self) -> str:
        result = self.client._run(
            "-s", self.serial, "shell", "cat", self._dump_path, timeout=10
        )
        return result.stdout

    def find_element(self, text: str = None, resource_id: str = None,
                     content_desc: str = None) -> list[dict]:
        """Search the UI hierarchy for matching elements."""
        import xml.etree.ElementTree as ET
        xml = self.dump_hierarchy()
        try:
            root = ET.fromstring(xml)
        except ET.ParseError:
            return []

        results = []
        for el in root.iter("node"):
            if text and el.attrib.get("text") == text:
                results.append(dict(el.attrib))
            elif resource_id and el.attrib.get("resource-id", "").endswith(resource_id):
                results.append(dict(el.attrib))
            elif content_desc and el.attrib.get("content-desc") == content_desc:
                results.append(dict(el.attrib))
        return results
