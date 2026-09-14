import unittest

from core.dag_scheduler import DAGScheduler


class TestDAGScheduler(unittest.TestCase):
    def setUp(self):
        self.scheduler = DAGScheduler(max_parallel_skills=4)

    def test_first_independent_steps_are_ready(self):
        steps = [
            {"step": 1, "skill": "skill-a", "status": "pending", "depends_on": []},
            {"step": 2, "skill": "skill-b", "status": "pending", "depends_on": []},
            {"step": 3, "skill": "skill-c", "status": "pending", "depends_on": [1, 2]},
        ]

        ready = self.scheduler.ready_steps(steps)

        self.assertEqual([step["step"] for step in ready], [1, 2])

    def test_dependent_step_unlocks_after_dependencies_complete(self):
        steps = [
            {"step": 1, "skill": "skill-a", "status": "completed", "depends_on": []},
            {"step": 2, "skill": "skill-b", "status": "completed", "depends_on": []},
            {"step": 3, "skill": "skill-c", "status": "pending", "depends_on": [1, 2]},
        ]

        ready = self.scheduler.ready_steps(steps)

        self.assertEqual([step["step"] for step in ready], [3])

    def test_running_steps_reduce_parallel_capacity(self):
        scheduler = DAGScheduler(max_parallel_skills=2)

        steps = [
            {"step": 1, "skill": "skill-a", "status": "running", "depends_on": []},
            {"step": 2, "skill": "skill-b", "status": "pending", "depends_on": []},
            {"step": 3, "skill": "skill-c", "status": "pending", "depends_on": []},
        ]

        ready = scheduler.ready_steps(steps)

        self.assertEqual([step["step"] for step in ready], [2])

    def test_max_parallel_skills_limits_ready_steps(self):
        scheduler = DAGScheduler(max_parallel_skills=2)

        steps = [
            {"step": 1, "skill": "skill-a", "status": "pending", "depends_on": []},
            {"step": 2, "skill": "skill-b", "status": "pending", "depends_on": []},
            {"step": 3, "skill": "skill-c", "status": "pending", "depends_on": []},
        ]

        ready = scheduler.ready_steps(steps)

        self.assertEqual([step["step"] for step in ready], [1, 2])


    def test_rejects_unknown_dependency(self):
        steps = [
            {
                "step": 1,
                "skill": "skill-a",
                "status": "pending",
                "depends_on": [99],
                "execution_mode": "ordered",
            },
        ]

        with self.assertRaises(ValueError):
            self.scheduler.validate(steps)


    def test_rejects_cyclic_dependency(self):
        steps = [
            {"step": 1, "skill": "skill-a", "status": "pending", "depends_on": [2]},
            {"step": 2, "skill": "skill-b", "status": "pending", "depends_on": [1]},
        ]
        with self.assertRaises(ValueError):
            self.scheduler.validate(steps)


if __name__ == "__main__":
    unittest.main()
