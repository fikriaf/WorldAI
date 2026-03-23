from typing import Optional
from collections import defaultdict
from ..types import Agent, AgentID


class SpeciationTracker:
    def __init__(self):
        self.species: dict[str, list[AgentID]] = defaultdict(list)
        self.genome_signatures: dict[AgentID, str] = {}
        self.species_phenotypes: dict[str, dict] = {}

    def register_agent(self, agent: Agent) -> str:
        signature = self._compute_signature(agent)
        self.genome_signatures[agent.id] = signature

        species = self._classify_by_signature(signature)

        if agent.id not in self.species[species]:
            self.species[species].append(agent.id)

        self._update_phenotype(species, agent)

        return species

    def remove_agent(self, agent_id: AgentID):
        if agent_id in self.genome_signatures:
            signature = self.genome_signatures[agent_id]
            species = self._classify_by_signature(signature)

            if agent_id in self.species[species]:
                self.species[species].remove(agent_id)

            del self.genome_signatures[agent_id]

    def _compute_signature(self, agent: Agent) -> str:
        gene_types = defaultdict(int)
        for gene in agent.genome.genes:
            gene_types[gene.product_type] += 1
            gene_types[gene.is_active] += 1

        signature_parts = [
            f"genes:{len(agent.genome.genes)}",
            f"complexity:{agent.neural_complexity}",
            f"mass:{agent.mass:.1f}",
            f"type:{'-'.join(f'{k}:{v}' for k, v in sorted(gene_types.items()))}",
        ]

        return "|".join(signature_parts)

    def _classify_by_signature(self, signature: str) -> str:
        if "genes:5:" in signature and "complexity:3" in signature:
            return "Microbial"
        elif "genes:10:" in signature:
            return "Protozoa"
        elif "complexity:8" in signature or "complexity:10" in signature:
            return "Multicellular"
        elif "type:neural:3" in signature or "type:neural:5" in signature:
            return "Neural"
        elif "mass:2.0" in signature or "mass:3.0" in signature:
            return "Macroorganism"
        else:
            return "Unclassified"

    def _update_phenotype(self, species: str, agent: Agent):
        if species not in self.species_phenotypes:
            self.species_phenotypes[species] = {
                "avg_energy": [],
                "avg_health": [],
                "avg_mass": [],
                "avg_genes": [],
                "count": 0,
            }

        ph = self.species_phenotypes[species]
        ph["avg_energy"].append(agent.energy)
        ph["avg_health"].append(agent.health)
        ph["avg_mass"].append(agent.mass)
        ph["avg_genes"].append(len(agent.genome.genes))
        ph["count"] += 1

        if len(ph["avg_energy"]) > 100:
            ph["avg_energy"] = ph["avg_energy"][-100:]
            ph["avg_health"] = ph["avg_health"][-100:]
            ph["avg_mass"] = ph["avg_mass"][-100:]
            ph["avg_genes"] = ph["avg_genes"][-100:]

    def get_species_summary(self) -> dict:
        summary = {}
        for species, agent_ids in self.species.items():
            if not agent_ids:
                continue

            ph = self.species_phenotypes.get(species, {})

            summary[species] = {
                "population": len(agent_ids),
                "avg_energy": sum(ph.get("avg_energy", [0]))
                / max(1, len(ph.get("avg_energy", [1]))),
                "avg_health": sum(ph.get("avg_health", [0]))
                / max(1, len(ph.get("avg_health", [1]))),
                "avg_mass": sum(ph.get("avg_mass", [0])) / max(1, len(ph.get("avg_mass", [1]))),
                "avg_genes": sum(ph.get("avg_genes", [0])) / max(1, len(ph.get("avg_genes", [1]))),
            }

        return summary

    def get_dominant_species(self) -> Optional[tuple[str, int]]:
        if not self.species:
            return None

        max_pop = 0
        dominant = None

        for species, agents in self.species.items():
            if len(agents) > max_pop:
                max_pop = len(agents)
                dominant = species

        return (dominant, max_pop) if dominant else None


_speciation_tracker: Optional[SpeciationTracker] = None


def get_speciation_tracker() -> SpeciationTracker:
    global _speciation_tracker
    if _speciation_tracker is None:
        _speciation_tracker = SpeciationTracker()
    return _speciation_tracker
