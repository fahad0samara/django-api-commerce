from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from django.core.cache import cache
import logging
from .models import ForecastModel
from .services import ForecastingService
from .data_validation import DataValidator, DataPreprocessor

logger = logging.getLogger(__name__)

class ModelSelector:
    """Automated model selection for forecasting"""
    
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.validator = DataValidator(data)
        self.preprocessor = DataPreprocessor()
        self.best_model: Optional[Dict] = None
        self.model_scores: Dict[str, Dict] = {}
    
    def select_best_model(self) -> Optional[Dict]:
        """Select the best forecasting model"""
        try:
            # Validate and clean data
            if not self.validator.validate_data():
                logger.warning("Data validation failed")
                return None
            
            cleaned_data = self.validator.clean_data()
            
            # Detect data characteristics
            characteristics = self._analyze_data_characteristics(cleaned_data)
            
            # Get candidate models based on data characteristics
            candidates = self._get_candidate_models(characteristics)
            
            # Evaluate candidates
            self.model_scores = self._evaluate_models(
                cleaned_data,
                candidates
            )
            
            # Select best model
            self.best_model = self._select_model(self.model_scores)
            
            return self.best_model
            
        except Exception as e:
            logger.error(f"Error in model selection: {str(e)}", exc_info=True)
            return None
    
    def _analyze_data_characteristics(
        self,
        data: pd.DataFrame
    ) -> Dict[str, any]:
        """Analyze characteristics of the data"""
        try:
            characteristics = {}
            
            # Check for seasonality
            seasonality_scores = self.preprocessor.detect_seasonality(data)
            characteristics['has_seasonality'] = any(
                score > 0.5 for score in seasonality_scores.values()
            )
            characteristics['seasonality_periods'] = [
                period for period, score in seasonality_scores.items()
                if score > 0.5
            ]
            
            # Check for trend
            trend, seasonal, residual = self.preprocessor.decompose_time_series(
                data
            )
            if trend is not None:
                characteristics['has_trend'] = abs(
                    trend.iloc[-1] - trend.iloc[0]
                ) > (trend.std() * 2)
            
            # Check for stationarity
            characteristics['is_stationary'] = self._check_stationarity(data)
            
            # Check data size
            characteristics['data_size'] = len(data)
            
            # Check for gaps
            characteristics['has_gaps'] = data.index.to_series().diff().max() > pd.Timedelta(days=1)
            
            return characteristics
            
        except Exception as e:
            logger.error(
                f"Error analyzing data characteristics: {str(e)}",
                exc_info=True
            )
            return {}
    
    def _get_candidate_models(
        self,
        characteristics: Dict[str, any]
    ) -> List[str]:
        """Get candidate models based on data characteristics"""
        candidates = []
        
        try:
            # Prophet is good for data with multiple seasonality patterns
            if characteristics.get('has_seasonality'):
                candidates.append('prophet')
            
            # ARIMA is good for stationary data or data that can be made stationary
            if characteristics.get('is_stationary'):
                candidates.append('arima')
            
            # Exponential smoothing is good for data with trend and/or seasonality
            if characteristics.get('has_trend') or characteristics.get('has_seasonality'):
                candidates.append('exp_smoothing')
            
            # Moving average for simple patterns or small datasets
            if characteristics.get('data_size', 0) < 90:
                candidates.append('moving_avg')
            
            # If no specific candidates, use all models
            if not candidates:
                candidates = ['prophet', 'arima', 'exp_smoothing', 'moving_avg']
            
            return candidates
            
        except Exception as e:
            logger.error(
                f"Error getting candidate models: {str(e)}",
                exc_info=True
            )
            return ['exp_smoothing']  # Default to exp_smoothing
    
    def _evaluate_models(
        self,
        data: pd.DataFrame,
        candidates: List[str]
    ) -> Dict[str, Dict]:
        """Evaluate candidate models using time series cross-validation"""
        scores = {}
        
        try:
            # Set up time series cross-validation
            tscv = TimeSeriesSplit(
                n_splits=min(5, len(data) // 30)  # At least 30 days per split
            )
            
            for algorithm in candidates:
                algorithm_scores = []
                
                for train_idx, test_idx in tscv.split(data):
                    train_data = data.iloc[train_idx]
                    test_data = data.iloc[test_idx]
                    
                    # Generate forecast
                    forecast_method = getattr(
                        ForecastingService,
                        f'_{algorithm}_forecast'
                    )
                    forecast = forecast_method(
                        train_data,
                        len(test_data)
                    )
                    
                    if forecast:
                        # Calculate errors
                        predicted = np.array([f[0] for f in forecast])
                        actual = test_data['quantity_sold'].values
                        
                        mape = np.mean(
                            np.abs(
                                (actual - predicted) /
                                np.where(actual == 0, 1, actual)
                            )
                        ) * 100
                        rmse = np.sqrt(
                            np.mean((actual - predicted) ** 2)
                        )
                        
                        algorithm_scores.append({
                            'mape': mape,
                            'rmse': rmse
                        })
                
                if algorithm_scores:
                    scores[algorithm] = {
                        'mape': np.mean([s['mape'] for s in algorithm_scores]),
                        'rmse': np.mean([s['rmse'] for s in algorithm_scores]),
                        'std_mape': np.std([s['mape'] for s in algorithm_scores]),
                        'std_rmse': np.std([s['rmse'] for s in algorithm_scores])
                    }
            
            return scores
            
        except Exception as e:
            logger.error(f"Error evaluating models: {str(e)}", exc_info=True)
            return {}
    
    def _select_model(self, scores: Dict[str, Dict]) -> Optional[Dict]:
        """Select the best model based on evaluation scores"""
        try:
            if not scores:
                return None
            
            # Calculate composite score (lower is better)
            composite_scores = {}
            for algorithm, metrics in scores.items():
                # Normalize MAPE and RMSE
                normalized_mape = metrics['mape'] / max(
                    s['mape'] for s in scores.values()
                )
                normalized_rmse = metrics['rmse'] / max(
                    s['rmse'] for s in scores.values()
                )
                
                # Consider stability (lower std is better)
                stability_penalty = (
                    metrics['std_mape'] / metrics['mape'] +
                    metrics['std_rmse'] / metrics['rmse']
                ) / 2
                
                composite_scores[algorithm] = (
                    0.4 * normalized_mape +
                    0.4 * normalized_rmse +
                    0.2 * stability_penalty
                )
            
            # Select best model
            best_algorithm = min(
                composite_scores.items(),
                key=lambda x: x[1]
            )[0]
            
            return {
                'algorithm': best_algorithm,
                'metrics': scores[best_algorithm]
            }
            
        except Exception as e:
            logger.error(f"Error selecting model: {str(e)}", exc_info=True)
            return None
    
    def _check_stationarity(self, data: pd.DataFrame) -> bool:
        """Check if the time series is stationary"""
        try:
            from statsmodels.tsa.stattools import adfuller
            
            # Perform Augmented Dickey-Fuller test
            result = adfuller(data['quantity_sold'].values)
            
            # p-value < 0.05 indicates stationarity
            return result[1] < 0.05
            
        except Exception as e:
            logger.error(f"Error checking stationarity: {str(e)}", exc_info=True)
            return False
    
    def get_model_comparison(self) -> Dict[str, Dict]:
        """Get detailed model comparison"""
        return self.model_scores
    
    def get_selection_summary(self) -> Dict[str, any]:
        """Get summary of model selection process"""
        if not self.best_model:
            return {}
        
        return {
            'selected_model': self.best_model['algorithm'],
            'metrics': self.best_model['metrics'],
            'validation_summary': self.validator.get_validation_summary(),
            'cleaning_actions': self.validator.get_cleaning_summary()
        }
