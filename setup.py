from setuptools import setup, find_packages


setup(
        name='PyERF',
        version='0.2',
        description='Python Embodied Robotics Framework',
        author='Felix Woolford',
        packages=find_packages(),
        install_requires=[
            'numpy',
            'vispy',
            'matplotlib',
            'pyqt5',
        ]
    )
