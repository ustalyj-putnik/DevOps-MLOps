from tsfresh import extract_features, select_features
from tsfresh.utilities.dataframe_functions import impute

def extract_tsfresh_features(X, y):
    """
    Извлекает признаки tsfresh из длинного формата X и выбирает релевантные по отношению к y.
    """
    # Извлечение всех признаков
    X_features = extract_features(
        X, 
        column_id='id', 
        column_sort='time', 
        disable_progressbar=True
    )

    # Заполнение NaN
    impute(X_features)

    # Отбор признаков по значимости относительно целевой переменной y
    X_selected = select_features(X_features, y)


    return X_selected
