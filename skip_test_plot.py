import unittest
import matplotlib.pyplot as plt


class MyTestCase(unittest.TestCase):
    def test_plot(self):

        x_values = [1, 2, 3, 4, 5, 6]
        y_values = [2, 4, 6, 8, 10, 8]

        f = plt.plot(x_values, y_values, label='Line Plot')

        plt.xlabel('X-axis Label')
        plt.ylabel('Y-axis Label')
        plt.title('Simple Line Plot')

        plt.legend()
        plt.show()


if __name__ == '__main__':
    unittest.main()
