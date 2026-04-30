from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List, Tuple, Union


class DataProcessor(ABC):
	def __init__(self) -> None:
		self._queue: List[Tuple[int, str]] = []
		self._next_rank = 0

	@abstractmethod
	def validate(self, data: Any) -> bool:
		raise NotImplementedError

	@abstractmethod
	def ingest(self, data: Any) -> None:
		raise NotImplementedError

	def output(self) -> tuple[int, str]:
		if not self._queue:
			raise ValueError("No data to output")
		return self._queue.pop(0)

	def _enqueue(self, values: Iterable[str]) -> None:
		for value in values:
			self._queue.append((self._next_rank, value))
			self._next_rank += 1


class NumericProcessor(DataProcessor):
	def validate(self, data: Any) -> bool:
		if self._is_number(data):
			return True
		if isinstance(data, list):
			return all(self._is_number(item) for item in data)
		return False

	def ingest(self, data: Union[int, float, List[Union[int, float]]]) -> None:
		if not self.validate(data):
			raise ValueError("Improper numeric data")
		if self._is_number(data):
			self._enqueue([str(data)])
			return
		self._enqueue([str(item) for item in data])

	@staticmethod
	def _is_number(value: Any) -> bool:
		return isinstance(value, (int, float)) and not isinstance(value, bool)


class TextProcessor(DataProcessor):
	def validate(self, data: Any) -> bool:
		if isinstance(data, str):
			return True
		if isinstance(data, list):
			return all(isinstance(item, str) for item in data)
		return False

	def ingest(self, data: Union[str, List[str]]) -> None:
		if not self.validate(data):
			raise ValueError("Improper text data")
		if isinstance(data, str):
			self._enqueue([data])
			return
		self._enqueue(list(data))


class LogProcessor(DataProcessor):
	def validate(self, data: Any) -> bool:
		if self._is_log_entry(data):
			return True
		if isinstance(data, list):
			return all(self._is_log_entry(item) for item in data)
		return False

	def ingest(self, data: Union[Dict[str, str], List[Dict[str, str]]]) -> None:
		if not self.validate(data):
			raise ValueError("Improper log data")
		if self._is_log_entry(data):
			self._enqueue([self._format_log_entry(data)])
			return
		self._enqueue([self._format_log_entry(item) for item in data])

	@staticmethod
	def _is_log_entry(value: Any) -> bool:
		if not isinstance(value, dict):
			return False
		return all(isinstance(key, str) and isinstance(val, str) for key, val in value.items())

	@staticmethod
	def _format_log_entry(entry: Dict[str, str]) -> str:
		if "log_level" in entry and "log_message" in entry:
			return f"{entry['log_level']}: {entry['log_message']}"
		return ", ".join(f"{key}: {val}" for key, val in entry.items())


def main() -> None:
	print("=== Code Nexus - Data Processor ===")

	numeric = NumericProcessor()
	text = TextProcessor()
	log = LogProcessor()

	print("Testing Numeric Processor...")
	print(f"Trying to validate input '42': {numeric.validate(42)}")
	print(f"Trying to validate input 'Hello': {numeric.validate('Hello')}")
	print("Test invalid ingestion of string 'foo' without prior validation:")
	try:
		numeric.ingest("foo")
	except ValueError as exc:
		print(f"Got exception: {exc}")
	print("Processing data: [1, 2, 3, 4, 5]")
	numeric.ingest([1, 2, 3, 4, 5])
	print("Extracting 3 values...")
	for _ in range(3):
		rank, value = numeric.output()
		print(f"Numeric value {rank}: {value}")

	print("Testing Text Processor...")
	print(f"Trying to validate input '42': {text.validate(42)}")
	print("Processing data: ['Hello', 'Nexus', 'World']")
	text.ingest(["Hello", "Nexus", "World"])
	print("Extracting 1 value...")
	rank, value = text.output()
	print(f"Text value {rank}: {value}")

	print("Testing Log Processor...")
	print(f"Trying to validate input 'Hello': {log.validate('Hello')}")
	log_entries = [
		{"log_level": "NOTICE", "log_message": "Connection to server"},
		{"log_level": "ERROR", "log_message": "Unauthorized access!!"},
	]
	print(f"Processing data: {log_entries}")
	log.ingest(log_entries)
	print("Extracting 2 values...")
	for _ in range(2):
		rank, value = log.output()
		print(f"Log entry {rank}: {value}")


if __name__ == "__main__":
	main()
