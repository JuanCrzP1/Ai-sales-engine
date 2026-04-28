import re
import unicodedata
from collections import Counter


SPANISH_STOPWORDS = {
	"de",
	"la",
	"el",
	"los",
	"las",
	"un",
	"una",
	"y",
	"a",
	"en",
	"del",
	"al",
	"que",
	"como",
	"por",
	"para",
}


def normalize_phone(phone_number: str) -> str:
	digits = re.sub(r"\D+", "", phone_number or "")
	return digits[-15:]


def normalize_text(text: str) -> str:
	normalized = unicodedata.normalize("NFKD", str(text or "").lower()).encode("ascii", "ignore").decode("ascii")
	return re.sub(r"\s+", " ", normalized).strip()


def tokenize(text: str) -> list[str]:
	return [token for token in re.findall(r"\w+", normalize_text(text)) if len(token) > 1 and token not in SPANISH_STOPWORDS]


def token_overlap_score(query: str, candidate: str) -> float:
	query_tokens = tokenize(query)
	candidate_tokens = tokenize(candidate)
	if not query_tokens or not candidate_tokens:
		return 0.0
	query_counter = Counter(query_tokens)
	candidate_counter = Counter(candidate_tokens)
	shared = sum((query_counter & candidate_counter).values())
	return shared / max(len(set(query_tokens)), 1)
