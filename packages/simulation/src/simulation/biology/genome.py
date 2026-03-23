from dataclasses import dataclass
from typing import Optional
import random
from ..types import Genome, Gene, SensoryCapabilities

SENSORY_GENE_TYPES = [
    "sensory_primitive",
    "sensory_chemical",
    "sensory_light",
    "sensory_thermal",
    "sensory_mechanical",
    "sensory_electromagnetic",
    "sensory_social",
    "sensory_magnetic",
    "sensory_auditory",
    "sensory_visual",
]


def create_initial_genome() -> Genome:
    genes = []
    for i in range(10):
        gene = Gene(
            id=f"g_{i:06d}",
            sequence=bytes([random.randint(0, 255) for _ in range(4)]),
            expression_level=random.random(),
            promoter_condition="default",
            product_type=random.choice(
                ["structural", "regulatory", "catalytic", "neural", "sensory_primitive"]
            ),
            is_active=True,
        )
        genes.append(gene)
    return Genome(genes=genes, mutation_rate=0.001, max_length=1000)


def decode_sensory_capabilities(genome: Genome) -> SensoryCapabilities:
    sensory_genes = [
        g
        for g in genome.genes
        if "sensory" in g.product_type or g.product_type == "sensory_primitive"
    ]
    if not sensory_genes:
        sensory_genes = genome.genes[:3]

    aggregate = sum(
        g.expression_level * (1.0 if g.is_active else 0.0) for g in sensory_genes
    ) / max(1, len(sensory_genes))

    caps = SensoryCapabilities.from_gene_value(aggregate)

    for gene in sensory_genes:
        pt = gene.product_type
        expr = gene.expression_level if gene.is_active else 0.0
        if pt == "sensory_chemical" or pt == "sensory_primitive":
            caps.chemical = min(1.0, caps.chemical * 0.5 + expr)
        elif pt == "sensory_light":
            caps.light = min(1.0, caps.light * 0.5 + expr)
        elif pt == "sensory_thermal":
            caps.thermal = min(1.0, expr)
        elif pt == "sensory_mechanical":
            caps.mechanical = min(1.0, expr)
        elif pt == "sensory_electromagnetic":
            caps.electromagnetic = min(1.0, expr)
        elif pt == "sensory_social":
            caps.social = min(1.0, expr)
        elif pt == "sensory_magnetic":
            caps.magnetic = min(1.0, expr)
        elif pt == "sensory_auditory":
            caps.auditory = min(1.0, expr)
        elif pt == "sensory_visual":
            caps.visual_range = min(1.0, expr)
        elif pt == "sensory_primitive":
            caps.proprioceptive = min(1.0, caps.proprioceptive * 0.5 + expr * 0.5)

    return caps


def mutate_sensory_gene(gene: Gene) -> Gene:
    new_seq = bytearray(gene.sequence)
    for _ in range(random.randint(1, 2)):
        idx = random.randint(0, len(new_seq) - 1)
        new_seq[idx] = min(255, new_seq[idx] + random.choice([-1, 1]))
    gene.sequence = bytes(new_seq)
    if random.random() < 0.05:
        gene.product_type = random.choice(
            SENSORY_GENE_TYPES + ["structural", "regulatory", "catalytic", "neural"]
        )
    if random.random() < 0.03 and "sensory" not in gene.product_type:
        gene.product_type = random.choice(SENSORY_GENE_TYPES)
    gene.expression_level = max(0.0, min(1.0, gene.expression_level + random.uniform(-0.1, 0.1)))
    gene.is_active = random.random() > 0.05 or gene.is_active
    return gene
