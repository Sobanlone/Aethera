from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class KnowledgeEntry:
    title: str
    source: str
    summary: str
    url: str | None = None


class EnvironmentalKnowledgeBase:
    def __init__(self) -> None:
        self.entries = [
            KnowledgeEntry(
                title="UNEP: The state of the environment",
                source="UNEP",
                summary="Healthy ecosystems support biodiversity, clean water, climate stability, and human well-being. Environmental degradation can reduce resilience and worsen ecosystem services.",
                url="https://www.unep.org/",
            ),
            KnowledgeEntry(
                title="Biodiversity and ecosystem services",
                source="IPBES / UNEP",
                summary="Biodiversity loss weakens ecosystem functions such as pollination, soil fertility, water purification, and natural hazard regulation.",
                url="https://www.unep.org/resources/report/global-assessment-report-biodiversity-ecosystem-services",
            ),
            KnowledgeEntry(
                title="Waste and pollution management",
                source="UNEP",
                summary="Improper disposal of waste, plastics, and chemicals can contaminate land and water, harm wildlife, and create long-term environmental risks.",
                url="https://www.unep.org/topics/waste-management",
            ),
            KnowledgeEntry(
                title="Deforestation and habitat loss",
                source="FAO / UNEP",
                summary="Deforestation and habitat fragmentation reduce biodiversity, increase erosion and greenhouse gas emissions, and degrade ecosystem connectivity.",
                url="https://www.fao.org/forestry/en/",
            ),
            KnowledgeEntry(
                title="Water quality and aquatic ecosystems",
                source="UNEP / WHO",
                summary="Water pollution from waste, runoff, and chemicals can harm fish, amphibians, and aquatic plant communities and reduce water quality for people and wildlife.",
                url="https://www.who.int/news-room/fact-sheets/detail/drinking-water",
            ),
        ]

    def retrieve(self, query: str) -> List[KnowledgeEntry]:
        query_lower = query.lower()
        query_terms = [term for term in query_lower.split() if len(term) > 3]
        matches: List[KnowledgeEntry] = []
        for entry in self.entries:
            haystack = " ".join([entry.title, entry.source, entry.summary]).lower()
            if not query_terms:
                continue
            score = 0
            for term in query_terms:
                if term in haystack:
                    score += 1
            if score > 0:
                matches.append((score, entry))

        ranked = sorted(matches, key=lambda item: item[0], reverse=True)
        return [entry for _, entry in ranked[:3]]
