from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List, Tuple, Union


class DataProcessor(ABC):
	def __init__(self, name: str) -> None:
		self._name = name
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

	def processor_name(self) -> str:
		return self._name

	def total_processed(self) -> int:
		return self._next_rank

	def remaining(self) -> int:
		return len(self._queue)

	def _enqueue(self, values: Iterable[str]) -> None:
		for value in values:
			self._queue.append((self._next_rank, value))
			self._next_rank += 1


class NumericProcessor(DataProcessor):
	def __init__(self) -> None:
		super().__init__("Numeric Processor")

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
	def __init__(self) -> None:
		super().__init__("Text Processor")

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
	def __init__(self) -> None:
		super().__init__("Log Processor")

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


class DataStream:
	def __init__(self) -> None:
		self._processors: List[DataProcessor] = []

	def register_processor(self, proc: DataProcessor) -> None:
		self._processors.append(proc)

	def process_stream(self, stream: list[Any]) -> None:
		for element in stream:
			handled = False
			for proc in self._processors:
				if proc.validate(element):
					try:
						proc.ingest(element)
						handled = True
					except ValueError:
						handled = False
					break
			if not handled:
				print(f"DataStream error - Can't process element in stream: {element}")

	def print_processors_stats(self) -> None:
		print("== DataStream statistics ==")
		if not self._processors:
			print("No processor found, no data")
			return
		for proc in self._processors:
			print(
				f"{proc.processor_name()}: total {proc.total_processed()} items processed, "
				f"remaining {proc.remaining()} on processor"
			)


def main() -> None:
	print("=== Code Nexus - Data Stream ===")
	print("Initialize Data Stream...")

	stream = DataStream()
	stream.print_processors_stats()

	print("Registering Numeric Processor")
	numeric = NumericProcessor()
	stream.register_processor(numeric)

	batch = [
		"Hello world",
		[3.14, -1, 2.71],
		[
			{"log_level": "WARNING", "log_message": "Telnet access! Use ssh instead"},
			{"log_level": "INFO", "log_message": "User wil is connected"},
		],
		42,
		["Hi", "five"],
	]
	print(f"Send first batch of data on stream: {batch}")
	stream.process_stream(batch)
	stream.print_processors_stats()

	print("Registering other data processors")
	text = TextProcessor()
	log = LogProcessor()
	stream.register_processor(text)
	stream.register_processor(log)

	print("Send the same batch again")
	stream.process_stream(batch)
	stream.print_processors_stats()

	print("Consume some elements from the data processors: Numeric 3, Text 2, Log 1")
	for _ in range(3):
		numeric.output()
	for _ in range(2):
		text.output()
	log.output()
	stream.print_processors_stats()


if __name__ == "__main__":
	main()
