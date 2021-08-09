import setuptools

def main():
    kwargs = {
        'name': 'patches',
        'version': '0.3',
        'packages': setuptools.find_packages(),
        'scripts': ['patches'],
    }
    setuptools.setup(**kwargs)

if __name__ == '__main__':
    main()
