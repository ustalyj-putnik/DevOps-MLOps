import pandas as pd

def create_tsfresh_dataset(df, window_size):
    """
    Преобразует DataFrame с колонками ['Date','Close'] в формат для tsfresh.
    Возвращает X (long-format DataFrame с ['id','time','value']) и y (Series меток).
    """
    df = df.sort_values('Date').reset_index(drop=True)
    data = []
    labels = []
    for i in range(len(df) - window_size):
        window = df['Close'].iloc[i:i+window_size].values
        label = df['Close'].iloc[i+window_size]
        for t, value in enumerate(window):
            data.append({'id': i, 'time': t, 'value': value})
        labels.append(label)
    X = pd.DataFrame(data)
    y = pd.Series(labels, index=range(len(labels)), name='target')
    return X, y
