"""
Module for testing 'model.py'.
"""

import unittest
import warnings
import random
import torch
from torch import nn
from brainspy.utils.pytorch import TorchUtils
from brainspy.processors.simulation.model import NeuralNetworkModel


class ModelTest(unittest.TestCase):
    """
    Class for testing 'model.py'.
    """
    def test_init_default(self):
        """
        Test to generate a model with default parameters raises 4 warnings
        and is an instance of nn.Sequential
        """
        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always")
            model = NeuralNetworkModel({})
            self.assertEqual(len(caught_warnings), 4)
        self.assertFalse(model.verbose)
        isinstance(model.raw_model, nn.Sequential)

    def test_init_none(self):
        """
        Test to generate a model with none as an argument raises 4 warnings
        and generates a model with default parameters
        """
        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always")
            model = NeuralNetworkModel(None)
            self.assertEqual(len(caught_warnings), 4)
        self.assertFalse(model.verbose)
        isinstance(model.raw_model, nn.Sequential)

    def test_init_dict(self):
        """
        Test to generate a model with a dict raises no warnings
        """
        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always")
            model_structure = {
                "D_in": 7,
                "D_out": 1,
                "activation": "relu",
                "hidden_sizes": [20, 20, 20]
            }
            model = NeuralNetworkModel(model_structure, True)
            self.assertEqual(len(caught_warnings), 0)
        self.assertTrue(model.verbose)
        """
        Test to generate a model with partial dict raises warnings
        """
        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always")
            model_structure = {
                "activation": "relu",
                "hidden_sizes": [20, 20, 20]
            }
            model = NeuralNetworkModel(model_structure, True)
            self.assertEqual(len(caught_warnings), 2)

    def test_init_negative(self):
        """
        Test to generate a model with negative values for D_in and D_out
        raises Assertion error
        """
        model_structure = {
            "D_in": random.randint(-10, -1),
            "D_out": random.randint(-10, -1),
            "activation": "relu",
            "hidden_sizes": [20, 20, 20]
        }
        with self.assertRaises(AssertionError):
            NeuralNetworkModel(model_structure)

    def test_init_zero_element(self):
        """
        If D_out or D_in are 0 , a warning is raised:
        Initializing zero-element tensors is a no-op
        """
        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always")
            model_structure = {
                "D_in": 5,
                "D_out": 0,
                "activation": "relu",
                "hidden_sizes": [20, 20, 20]
            }
            NeuralNetworkModel(model_structure)
            self.assertEqual(len(caught_warnings), 1)
        """
        If hidden sizes contains 0 , a warning is raised:
        Initializing zero-element tensors is a no-op
        """
        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always")
            model_structure = {
                "D_in": 7,
                "D_out": 1,
                "activation": "relu",
                "hidden_sizes": [20, 20, 0]
            }
            NeuralNetworkModel(model_structure)
            self.assertEqual(len(caught_warnings), 2)

    def test_init_fail(self):
        """
        Invalid type for D_in or D_out raises an AssertionError
        """
        model_structure = {
            "D_in": "Invalid type",
            "D_out": "Invalid type",
            "activation": "relu",
            "hidden_sizes": [20, 20, 0]
        }
        with self.assertRaises(AssertionError):
            NeuralNetworkModel(model_structure)

    def test_init_fail_2(self):
        """
        Invalid type for hidden sizes raises an AssertionError
        """
        model_structure = {
            "D_in": 7,
            "D_out": 1,
            "activation": "relu",
            "hidden_sizes": "invalid type"
        }
        with self.assertRaises(AssertionError):
            NeuralNetworkModel(model_structure)

        model_structure = {
            "D_in": 7,
            "D_out": 1,
            "activation": "relu",
            "hidden_sizes": [1, 2, 3, "invalid type"]
        }
        with self.assertRaises(AssertionError):
            NeuralNetworkModel(model_structure)

    def test_init_random(self):
        """
        Test to generate a model with random values for D_in,
        D_out and hidden_sizes
        If the method fails, the cpu cannot allocate enough bytes
        """
        threshold_electrodes = 20
        threshold_hidden_sizes = 90
        threshold_hidden_layer_no = 10
        model_structure = {
            "D_in":
            random.randint(0, threshold_electrodes),
            "D_out":
            random.randint(0, threshold_electrodes),
            "activation":
            "relu",
            "hidden_sizes": [
                random.randint(0, threshold_hidden_sizes)
                for i in range(threshold_hidden_layer_no)
            ]
        }
        try:
            NeuralNetworkModel(model_structure)
        except (Exception):
            self.fail(
                "Could not generate model : DefaultCPUAllocator: not enough memory"
            )

    def test_init_type_dict_typeerror(self):
        """
        Invalid type for model_structure dict raises TypeError
        """
        with self.assertRaises(TypeError):
            NeuralNetworkModel("Invalid type")
        with self.assertRaises(TypeError):
            NeuralNetworkModel([1, 2, 3, 4])

    def test_build_model_structure(self):
        """
        Test build_model_structure and checking length of raw model:
        input layer, 6 activations, 5 hidden layers, output layer
        """
        model = NeuralNetworkModel({})
        raw = model.raw_model
        self.assertEqual(len(raw), 13)

    def test_get_activation(self):
        """
        Test get_activation.
        """
        model = NeuralNetworkModel({})
        self.assertIsInstance(model._get_activation("relu"), nn.ReLU)
        self.assertIsInstance(model._get_activation("elu"), nn.ELU)
        self.assertIsInstance(model._get_activation("tanh"), nn.Tanh)
        self.assertIsInstance(model._get_activation("hard-tanh"), nn.Hardtanh)
        self.assertIsInstance(model._get_activation("sigmoid"), nn.Sigmoid)

    def test_activation_default(self):
        """
        Invalid type for get_activation raises a warning and returns
        nn.Relu activation type
        """
        model = NeuralNetworkModel({})
        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always")
            self.assertIsInstance(model._get_activation("test"), nn.ReLU)
            self.assertEqual(len(caught_warnings), 1)

        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always")
            self.assertIsInstance(model._get_activation([1, 2, 3, 4]), nn.ReLU)
            self.assertEqual(len(caught_warnings), 1)

        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always")
            self.assertIsInstance(model._get_activation(None), nn.ReLU)
            self.assertEqual(len(caught_warnings), 1)

    def test_consistency_check(self):
        """
        Test if info_consistency_check makes the necessary adjustments.
        """
        model = NeuralNetworkModel({})
        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always")
            d = {}
            model.structure_consistency_check(d)
            self.assertTrue("D_out" in d)
            self.assertTrue("hidden_sizes" in d)
            self.assertTrue("activation" in d)
            self.assertEqual(len(caught_warnings), 4)

    def test_consistancy_check_typeerror(self):
        """
        Invalid type for structure_consistency_check raises TypeError
        """
        model = NeuralNetworkModel({})
        with self.assertRaises(TypeError):
            model.structure_consistency_check(None)
        with self.assertRaises(TypeError):
            model.structure_consistency_check([1, 2, 3, 4])
        with self.assertRaises(TypeError):
            model.structure_consistency_check("Invalid type")

    def test_forward(self):
        """
        Test the forward pass, check whether result has right shape.
        """
        model = NeuralNetworkModel({})
        for i in range(1, 1000):
            x = torch.rand((7))
            result = model.forward(x)
            test = torch.rand((1))
            self.assertEqual(result.shape, test.shape)

    def test_forward_fail(self):
        """
        Invalid size for torch tensor raises Runtime error
        """
        test_sizes = ((1, 1), (10, 1), (100, 1), (10, 2))
        for size in test_sizes:
            model = NeuralNetworkModel({})
            x = torch.rand(size,
                           device=TorchUtils.get_device(),
                           dtype=torch.get_default_dtype())
            with self.assertRaises(RuntimeError):
                model.forward(x)

    def test_forward_typeerror(self):
        """
        Invalid type for forward pass raises TypeError
        """
        model = NeuralNetworkModel({})
        x = [1, 2, 3, 4]
        with self.assertRaises(TypeError):
            model.forward(x)
        x = None
        with self.assertRaises(TypeError):
            model.forward(x)
        x = "Invalid type"
        with self.assertRaises(TypeError):
            model.forward(x)


if __name__ == "__main__":
    unittest.main()
