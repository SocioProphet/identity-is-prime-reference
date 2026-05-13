from __future__ import annotations

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from prime_er.behavior import behavioral_similarity, delay_vectors
from prime_er.edit_geometry import approximate_record_path_cost, path_score
from prime_er.entity_geometry import EntityState, approximate_entity_path_cost, local_expansion_exponent
from prime_er.neutrality import neutrality_replay_certificate


class ERPlusGeometryTests(unittest.TestCase):
    def test_record_path_cost_reaches_canonical_name(self) -> None:
        source = {"name": "Mike", "phone": "+1 (215) 555-0100"}
        target = {"name": "Michael", "phone": "12155550100"}
        result = approximate_record_path_cost(source, target, keys=["name", "phone"])
        self.assertTrue(result.reachable)
        self.assertAlmostEqual(result.cost, 0.7)
        self.assertGreater(path_score(result), 0.0)
        self.assertEqual(result.certificate["artifact_type"], "RecordPathCertificate")

    def test_entity_path_cost_tracks_membership_delta(self) -> None:
        source = EntityState.of("e1", ["r1", "r2"], {"dob": "1980-01-01"})
        target = EntityState.of("e2", ["r2", "r3"], {"dob": "1980-01-01"})
        result = approximate_entity_path_cost(source, target)
        self.assertTrue(result.reachable)
        self.assertEqual(result.cost, 2.0)
        self.assertEqual([step.move_type for step in result.steps], ["drop_record", "add_record"])

    def test_local_expansion_exponent_is_finite_graph_diagnostic(self) -> None:
        delta = local_expansion_exponent(2, 8, 1.0, 2.0)
        self.assertGreater(delta, 1.0)

    def test_behavioral_similarity_prefers_nearby_delay_clouds(self) -> None:
        left = delay_vectors([1, 2, 3, 4, 5], tau=1, dimension=2)
        near = delay_vectors([1, 2, 3, 4.1, 5.1], tau=1, dimension=2)
        far = delay_vectors([10, 20, 30, 40, 50], tau=1, dimension=2)
        self.assertGreater(behavioral_similarity(left, near), behavioral_similarity(left, far))

    def test_neutrality_replay_certificate_detects_confluence(self) -> None:
        def reducer(state: dict[str, int], event: tuple[str, int]) -> dict[str, int]:
            out = dict(state)
            key, value = event
            out[key] = out.get(key, 0) + value
            return out

        cert = neutrality_replay_certificate({}, [("a", 1), ("b", 2)], [("b", 2), ("a", 1)], reducer)
        self.assertEqual(cert["result"], "VERIFIED")
        self.assertEqual(cert["distance"], 0.0)


if __name__ == "__main__":
    unittest.main()
