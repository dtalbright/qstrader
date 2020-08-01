from qstrader.alpha_model.alpha_model import AlphaModel


class TimeSignalsAlphaModel(AlphaModel):
    """
    A simple AlphaModel that provides a single scalar forecast
    value for each Asset in the Universe based on the time index
    and the data_handler.

    Parameters
    ----------
    signal : dict{str: dict{str, float}}
        The single fixed floating point scalar value for the signals, based on
        the key of type of strategy (defensive, balanced, aggressive).
    data_handler : `DataHandler`, 
        A pandas dataframe that has the portfolio type for every timestamp
    universe : `Universe`
        The Assets to make signal forecasts for.
    """

    def __init__(
        self,
        signal,
        data_handler,
        universe=None
    ):
        self.universe = universe
        self.signal = signal
        self.data_handler = data_handler

    def __call__(self, dt):
        """
        Produce the dictionary of single fixed scalar signals for
        each of the Asset instances within the Universe.

        Parameters
        ----------
        dt : `pd.Timestamp`
            The time 'now' used to obtain appropriate data and universe
            for the the signals.

        Returns
        -------
        `dict{str: float}`
            The Asset symbol keyed scalar-valued signals.
        """
        strategy = self.data_handler.iloc[self.data_handler.index.get_loc(dt, method='pad')]['strategy'] 
        print("TimeSignalsStrategy:")
        print(strategy)
        return self.signal.get(strategy)
