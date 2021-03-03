import setuptools

setuptools.setup(
    name='oe-edit',
    version='0.1.0',
    description='Old English editor',
    author='kovadarra',
    author_email='58000806+kovadarra@users.noreply.github.com',
    packages=setuptools.find_packages(),
    install_requires=[
        'PySimpleGUI>=4.34.0',
        'sortedcontainers>=2.3.0',
        'pywin32>=223'],
    python_requires='>=3.9',
    package_data={'': ['icon.ico', 'wordbook.bin']}
)
