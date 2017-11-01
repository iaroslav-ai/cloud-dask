# just a test hyperparameter search with dask
from sklearn.datasets import load_digits
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import GridSearchCV
from sklearn.svm import SVC

# define a test model
model = GridSearchCV(
    estimator=make_pipeline(
        StandardScaler(),
        SVC()
    ),
    param_grid={
        'svc__C': [4.0 ** i for i in range(-10, 10)],
        'svc__gamma': [4.0 ** i for i in range(-10, 10)],
    },
    n_jobs=-1,
    verbose=1000000
)

X, y = load_digits(10, True)

import distributed.joblib
from sklearn.externals.joblib import parallel_backend

dask_scheduler='192.168.0.88'

with parallel_backend('dask.distributed', scheduler_host=dask_scheduler+":8786"):
    model.fit(X, y)