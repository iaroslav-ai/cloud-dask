# just a test hyperparameter search with dask
from sklearn.datasets import load_digits
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import GridSearchCV
from sklearn.neural_network import MLPClassifier

# define a test model
model = GridSearchCV(
    estimator=make_pipeline(
        StandardScaler(),
        MLPClassifier()
    ),
    param_grid={
        'mlpclassifier__hidden_layer_sizes': [(i, ) for i in range(100, 200)],
    },
    n_jobs=-1,
    verbose=1000000
)

X, y = load_digits(10, True)

import distributed.joblib
from sklearn.externals.joblib import parallel_backend

dask_scheduler='192.168.0.88'

# seems to work best for length fit jobs
with parallel_backend('dask.distributed', scheduler_host=dask_scheduler+":8786", scatter=[X, y]):
    model.fit(X, y)
    print(model.best_params_)
    print(model.best_score_)
