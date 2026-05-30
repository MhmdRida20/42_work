import pandas # type: ignore
import numpy
import sys
from importlib import import_module, metadata
from matplotlib import pyplot

if __name__ == "__main__":

    print("LOADING STATUS: Loading programs...")
    print("Checking dependencies:")
    dependencies = ["pandas", "matplotlib", "numpy"]
    for dep in dependencies:
        try:
            import_module(dep)
            print(f"[OK] {dep} ({metadata.version(dep)})")
        except ImportError:
            print(f"Dependency '{dep}' is NOT installed."
                  "Please install it before running the program.")
            sys.exit(1)
    print("Analyzing Matrix data...")
    # Processing 500 data points...
    print("Processing 500 data points...")
    numpy.random.seed(0)
    # Simulate a dataset with 100 samples and 5 features
    data = numpy.random.rand(100, 5)
    # Create a pandas DataFrame from the simulated data
    df = pandas.DataFrame(data, columns=[f"Feature_{i}" for i in range(1, 6)])
    print(df.head())
    # Visualize the data
    pandas.plotting.scatter_matrix(df, figsize=(10, 10))
    save_path = "matrix_analysis.png"
    pyplot.savefig(save_path)
    pyplot.show()
    print("LOADING STATUS: Program loaded successfully!")
    print("Analysis complete!")
    print("Results saved to: matrix_analysis.png")
