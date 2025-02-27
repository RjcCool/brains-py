import unittest

import torch

import brainspy
from brainspy.utils.pytorch import TorchUtils
from brainspy.processors.processor import Processor


class ProcessorTest(unittest.TestCase):
    """
    Class for testing 'processor.py'.
    """
    def setUp(self):
        """
        Create different processors to run tests on.
        Tests init and load_processor methods for simulation and debug.
        Assume 7 activation electrodes and 1 output electrode.

        Do not create hardware processors here.
        """

        # define electrode effects
        self.clipping = [-114.0, 114.0]
        self.amplification = [28.5]
        self.voltages = [[-1.2, 0.6], [-1.2, 0.6], [-1.2, 0.6], [-1.2, 0.6],
                         [-1.2, 0.6], [-0.7, 0.3], [-0.7, 0.3]]

        # create electrode dictionaries
        electrode_effects = {
            "amplification": self.amplification,
            "output_clipping": self.clipping,
            "voltage_ranges": self.voltages,
            "noise": None
        }
        electrode_info = {
            'activation_electrodes': {
                'electrode_no': 7,
                'voltage_ranges': self.voltages
            },
            'output_electrodes': {
                'electrode_no': 1,
                'amplification': self.amplification,
                'clipping_value': self.clipping
            }
        }

        # define waveforms
        self.plateau = 80
        self.waveform = {"slope_length": 20, "plateau_length": self.plateau}

        # create config dictionaries
        self.configs_simulation = {
            "processor_type": "simulation",
            "electrode_effects": electrode_effects,
            "waveform": self.waveform,
            "driver": {}
        }
        self.configs_debug = {
            "processor_type": "simulation_debug",
            "electrode_effects": electrode_effects,
            "waveform": self.waveform,
            "driver": {}
        }

        # create model and info
        model_structure = {
            "D_in": 7,
            "D_out": 1,
            "activation": "relu",
            "hidden_sizes": [20, 20, 20]
        }
        self.info = {
            "model_structure": model_structure,
            "electrode_info": electrode_info
        }

        # create processors
        self.processor_simulation = Processor(self.configs_simulation,
                                              self.info)
        self.processor_debug = Processor(self.configs_debug, self.info)

        # define hardware configs
        instruments_setup_cdaq = {
            "activation_instrument": "cDAQ1Mod4",
            "activation_sampling_frequency": 10000,
            "activation_channels": [8, 10, 13, 11, 7, 12, 14],
            "activation_voltage_ranges": self.voltages,
            "readout_instrument": "cDAQ1Mod3",
            "readout_sampling_frequency": 10000,
            "readout_channels": [2],
            "trigger_source": "cDAQ1/segment1"
        }
        driver_cdaq = {
            "instruments_setup": instruments_setup_cdaq,
            "output_clipping_range": self.clipping,
            "amplification": self.amplification[0]
        }
        self.configs_cdaq = {
            "processor_type": "cdaq_to_cdaq",
            "electrode_effects": {},
            "waveform": self.waveform,
            "driver": driver_cdaq
        }
        instruments_setup_nidaq = {
            "activation_instrument": "dev1",
            "activation_sampling_frequency": 10000,
            "activation_channels": [0, 1, 2, 3, 4, 5, 6],
            "readout_instrument": "cDAQ1Mod1",
            "readout_sampling_frequency": 10000,
            "readout_channels": [0]
        }
        driver_nidaq = {
            "instruments_setup": instruments_setup_nidaq,
            "output_clipping_range": self.clipping,
            "amplification": self.amplification[0]
        }
        self.configs_nidaq = {
            "processor_type": "cdaq_to_nidaq",
            "electrode_effects": {},
            "waveform": self.waveform,
            "driver": driver_nidaq
        }

    @unittest.skipIf(brainspy.TEST_MODE != "HARDWARE_CDAQ",
                     "Hardware test is skipped for simulation setup.")
    def test_cdaq(self):
        """
        Test the creation of the cdaq to cdaq processor type.
        Also tests load_configs() and close().
        """
        processor = Processor(self.configs_cdaq, self.info)
        processor.close()

    @unittest.skipIf(brainspy.TEST_MODE != "HARDWARE_NIDAQ",
                     "Hardware test is skipped for simulation setup.")
    def test_nidaq(self):
        """
        Test the creation of the cdaq to nidaq processor type.
        Also tests load_configs() and close().
        """
        processor = Processor(self.configs_nidaq, self.info)
        processor.close()

    def test_load_processor(self):
        """
        Test if error is raised when processor type not recognized.
        """
        try:

            self.processor_simulation.load_processor(
                {"processor_type": "test"}, {})
            self.fail()
        except NotImplementedError:
            pass

    def test_forward(self):
        """
        Run forward pass and check shape of result. Takes into account the
        plateau length.
        """
        for i in range(1, 100):
            x = TorchUtils.format(torch.rand(i, 7))
            x = self.processor_simulation.forward(x)
            self.assertEqual(list(x.shape), [self.plateau * i, 1])
            x = TorchUtils.format(torch.rand(i, 7))
            x = self.processor_debug.forward(x)
            self.assertEqual(list(x.shape), [self.plateau * i, 1])

    @unittest.skipIf(brainspy.TEST_MODE != "HARDWARE_CDAQ",
                     "Hardware test is skipped for simulation setup.")
    def test_forward_cdaq(self):
        """
        Test the forward pass of the cdaq to cdaq processor.
        """
        processor = Processor(self.configs_cdaq, self.info)
        for i in range(1, 100):
            x = TorchUtils.format(torch.rand(i, 7))
            x = processor.forward(x)
            self.assertEqual(list(x.shape), [self.plateau * i, 1])
        processor.close()

    @unittest.skipIf(brainspy.TEST_MODE != "HARDWARE_NIDAQ",
                     "Hardware test is skipped for simulation setup.")
    def test_forward_nidaq(self):
        """
        Test the forward pass of the cdaq to nidaq processor.
        """
        processor = Processor(self.configs_nidaq, self.info)
        for i in range(1, 100):
            x = TorchUtils.format(torch.rand(i, 7))
            x = processor.forward(x)
            self.assertEqual(list(x.shape), [self.plateau * i, 1])
        processor.close()

    def test_format_targets(self):
        """
        Check shape of data transformed to plateaus.
        Is independent of type of processor.
        """
        for i in range(1, 100):
            x = TorchUtils.format(torch.rand(i, 7))
            x = self.processor_simulation.format_targets(x)
            self.assertEqual(list(x.shape), [self.plateau * i, 7])
            x = TorchUtils.format(torch.rand(i, 7))
            x = self.processor_debug.format_targets(x)
            self.assertEqual(list(x.shape), [self.plateau * i, 7])

    def test_get_voltage_ranges(self):
        """
        Test the method for getting the voltage ranges. Compare to the list
        used to create the processor.
        """
        target = TorchUtils.format(self.voltages)
        ranges = self.processor_simulation.get_voltage_ranges()
        self.assertTrue(torch.equal(ranges, target))
        ranges = self.processor_debug.get_voltage_ranges()
        self.assertTrue(torch.equal(ranges, target))

    @unittest.skipIf(brainspy.TEST_MODE != "HARDWARE_CDAQ",
                     "Hardware test is skipped for simulation setup.")
    def test_get_voltage_ranges_cdaq(self):
        """
        Test the method for getting the voltage ranges. Compare to the list
        used to create the processor.
        For cdaq to cdaq.
        """
        processor = Processor(self.configs_cdaq, self.info)
        target = TorchUtils.format(self.voltages)
        ranges = processor.get_voltage_ranges()
        self.assertTrue(torch.equal(ranges, target))
        processor.close()

    @unittest.skipIf(brainspy.TEST_MODE != "HARDWARE_NIDAQ",
                     "Hardware test is skipped for simulation setup.")
    def test_get_voltage_ranges_nidaq(self):
        """
        Test the method for getting the voltage ranges. Compare to the list
        used to create the processor.
        For cdaq to nidaq.
        """
        processor = Processor(self.configs_nidaq, self.info)
        target = TorchUtils.format(self.voltage)
        ranges = processor.get_voltage_ranges()
        self.assertTrue(torch.equal(ranges, target))
        processor.close()

    def test_get_activation_electrode_no(self):
        """
        Test the method for getting the number of activation electrodes,
        should be 7.
        """
        self.assertEqual(
            self.processor_simulation.get_activation_electrode_no(), 7)
        self.assertEqual(self.processor_debug.get_activation_electrode_no(), 7)

    @unittest.skipIf(brainspy.TEST_MODE != "HARDWARE_CDAQ",
                     "Hardware test is skipped for simulation setup.")
    def test_get_activation_electrode_no_cdaq(self):
        """
        Test the method for getting the number of activation electrodes,
        should be 7.
        For cdaq to cdaq.
        """
        processor = Processor(self.configs_cdaq, self.info)
        self.assertEqual(processor.get_activation_electrode_no(), 7)
        processor.close()

    @unittest.skipIf(brainspy.TEST_MODE != "HARDWARE_NIDAQ",
                     "Hardware test is skipped for simulation setup.")
    def test_get_activation_electrode_no_nidaq(self):
        """
        Test the method for getting the number of activation electrodes,
        should be 7.
        For cdaq to nidaq.
        """
        processor = Processor(self.configs_nidaq, self.info)
        self.assertEqual(processor.get_activation_electrode_no(), 7)
        processor.close()

    def test_get_clipping_value(self):
        """
        Test the method for getting the clipping value.
        """
        self.assertTrue(
            torch.equal(self.processor_simulation.get_clipping_value(),
                        TorchUtils.format(self.clipping)))
        self.assertTrue(
            torch.equal(self.processor_debug.get_clipping_value(),
                        TorchUtils.format(self.clipping)))

    @unittest.skipIf(brainspy.TEST_MODE != "HARDWARE_CDAQ",
                     "Hardware test is skipped for simulation setup.")
    def test_get_clipping_value_cdaq(self):
        """
        Test the method for getting the clipping value for cdaq to cdaq.
        """
        processor = Processor(self.configs_cdaq, self.info)
        self.assertTrue(
            torch.equal(processor.get_clipping_value(),
                        TorchUtils.format(self.clipping)))
        processor.close()

    @unittest.skipIf(brainspy.TEST_MODE != "HARDWARE_NIDAQ",
                     "Hardware test is skipped for simulation setup.")
    def test_get_clipping_value_nidaq(self):
        """
        Test the method for getting the clipping value for cdaq to nidaq.
        """
        processor = Processor(self.configs_nidaq, self.info)
        self.assertTrue(
            torch.equal(processor.get_clipping_value(),
                        TorchUtils.format(self.clipping)))
        processor.close()

    def test_swap(self):
        """
        Test swap method.
        """
        self.processor_simulation.swap(self.configs_simulation, self.info)
        self.processor_debug.swap(self.configs_simulation, self.info)

    @unittest.skipIf(brainspy.TEST_MODE != "HARDWARE_CDAQ",
                     "Hardware test is skipped for simulation setup.")
    def test_swap_cdaq(self):
        """
        Test swap method for cdaq to cdaq.
        """
        processor = Processor(self.configs_cdaq, self.info)
        processor.swap(self.configs_cdaq, self.info)
        processor.close()

    @unittest.skipIf(brainspy.TEST_MODE != "HARDWARE_NIDAQ",
                     "Hardware test is skipped for simulation setup.")
    def test_swap_nidaq(self):
        """
        Test swap method for cdaq to nidaq.
        """
        processor = Processor(self.configs_nidaq, self.info)
        processor.swap(self.configs_nidaq, self.info)
        processor.close()

    def test_is_hardware(self):
        """
        Test method for checking if processor is hardware.
        """
        self.assertFalse(self.processor_simulation.is_hardware())
        self.assertFalse(self.processor_debug.is_hardware())

    @unittest.skipIf(brainspy.TEST_MODE != "HARDWARE_CDAQ",
                     "Hardware test is skipped for simulation setup.")
    def test_is_hardware_cdaq(self):
        """
        Test method for checking if processor is hardware for cdaq to cdaq.
        """
        processor = Processor(self.configs_cdaq, self.info)
        self.assertTrue(processor.is_hardware())
        processor.close()

    @unittest.skipIf(brainspy.TEST_MODE != "HARDWARE_NIDAQ",
                     "Hardware test is skipped for simulation setup.")
    def test_is_hardware_nidaq(self):
        """
        Test method for checking if processor is hardware for cdaq to nidaq.
        """
        processor = Processor(self.configs_nidaq, self.info)
        self.assertTrue(processor.is_hardware())
        processor.close()

    def test_close(self):
        """
        Test method for closing processor.
        """
        self.processor_simulation.close()
        self.processor_debug.close()


if __name__ == "__main__":
    unittest.main()
