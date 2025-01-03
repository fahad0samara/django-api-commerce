import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class DataValidator:
    """Validate and clean time series data for forecasting"""
    
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.validation_results: Dict[str, bool] = {}
        self.cleaning_actions: List[str] = []
    
    def validate_data(self) -> bool:
        """Run all validation checks"""
        try:
            self.validation_results = {
                'has_minimum_records': self._check_minimum_records(),
                'has_valid_dates': self._check_date_validity(),
                'has_valid_values': self._check_value_validity(),
                'has_consistent_frequency': self._check_frequency_consistency(),
                'has_no_duplicates': self._check_duplicates()
            }
            
            return all(self.validation_results.values())
            
        except Exception as e:
            logger.error(f"Error in data validation: {str(e)}", exc_info=True)
            return False
    
    def clean_data(self) -> pd.DataFrame:
        """Clean the data based on validation results"""
        try:
            cleaned_data = self.data.copy()
            
            # Handle missing values
            cleaned_data = self._handle_missing_values(cleaned_data)
            
            # Remove duplicates
            if not self.validation_results.get('has_no_duplicates', True):
                cleaned_data = self._remove_duplicates(cleaned_data)
            
            # Handle outliers
            cleaned_data = self._handle_outliers(cleaned_data)
            
            # Ensure consistent frequency
            if not self.validation_results.get('has_consistent_frequency', True):
                cleaned_data = self._ensure_consistent_frequency(cleaned_data)
            
            # Ensure non-negative values
            cleaned_data = self._ensure_non_negative(cleaned_data)
            
            return cleaned_data
            
        except Exception as e:
            logger.error(f"Error in data cleaning: {str(e)}", exc_info=True)
            return self.data
    
    def _check_minimum_records(self, min_records: int = 30) -> bool:
        """Check if there are enough records for forecasting"""
        return len(self.data) >= min_records
    
    def _check_date_validity(self) -> bool:
        """Check if dates are valid and in chronological order"""
        try:
            dates = pd.to_datetime(self.data.index)
            is_monotonic = dates.is_monotonic_increasing
            is_valid = pd.notnull(dates).all()
            return is_monotonic and is_valid
        except Exception:
            return False
    
    def _check_value_validity(self) -> bool:
        """Check if values are valid numbers"""
        try:
            return pd.to_numeric(
                self.data['quantity_sold'],
                errors='coerce'
            ).notnull().all()
        except Exception:
            return False
    
    def _check_frequency_consistency(self) -> bool:
        """Check if data has consistent frequency"""
        try:
            dates = pd.to_datetime(self.data.index)
            diff = dates.diff()[1:]
            return diff.nunique() == 1
        except Exception:
            return False
    
    def _check_duplicates(self) -> bool:
        """Check for duplicate dates"""
        return not self.data.index.duplicated().any()
    
    def _handle_missing_values(self, data: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values in the data"""
        try:
            # Interpolate missing values
            data = data.interpolate(method='time')
            
            # Forward fill any remaining NAs at the start
            data = data.fillna(method='ffill')
            
            # Backward fill any remaining NAs at the end
            data = data.fillna(method='bfill')
            
            self.cleaning_actions.append("Handled missing values")
            return data
            
        except Exception as e:
            logger.error(f"Error handling missing values: {str(e)}", exc_info=True)
            return data
    
    def _remove_duplicates(self, data: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate dates"""
        try:
            data = data[~data.index.duplicated(keep='first')]
            self.cleaning_actions.append("Removed duplicate dates")
            return data
        except Exception as e:
            logger.error(f"Error removing duplicates: {str(e)}", exc_info=True)
            return data
    
    def _handle_outliers(
        self,
        data: pd.DataFrame,
        threshold: float = 3.0
    ) -> pd.DataFrame:
        """Handle outliers using z-score method"""
        try:
            z_scores = np.abs(
                (data - data.mean()) / data.std()
            )
            outliers = z_scores > threshold
            
            if outliers.any().any():
                # Replace outliers with rolling median
                window = 7  # 7-day window
                rolling_median = data.rolling(
                    window=window,
                    center=True,
                    min_periods=1
                ).median()
                
                data[outliers] = rolling_median[outliers]
                self.cleaning_actions.append(
                    f"Replaced {outliers.sum().sum()} outliers"
                )
            
            return data
            
        except Exception as e:
            logger.error(f"Error handling outliers: {str(e)}", exc_info=True)
            return data
    
    def _ensure_consistent_frequency(
        self,
        data: pd.DataFrame,
        freq: str = 'D'
    ) -> pd.DataFrame:
        """Ensure data has consistent frequency"""
        try:
            # Create full date range
            date_range = pd.date_range(
                start=data.index.min(),
                end=data.index.max(),
                freq=freq
            )
            
            # Reindex data
            data = data.reindex(date_range)
            
            # Handle any new missing values
            data = self._handle_missing_values(data)
            
            self.cleaning_actions.append("Ensured consistent frequency")
            return data
            
        except Exception as e:
            logger.error(
                f"Error ensuring consistent frequency: {str(e)}",
                exc_info=True
            )
            return data
    
    def _ensure_non_negative(self, data: pd.DataFrame) -> pd.DataFrame:
        """Ensure all values are non-negative"""
        try:
            negative_mask = data < 0
            if negative_mask.any().any():
                data[negative_mask] = 0
                self.cleaning_actions.append("Replaced negative values with 0")
            return data
        except Exception as e:
            logger.error(f"Error ensuring non-negative values: {str(e)}", exc_info=True)
            return data
    
    def get_validation_summary(self) -> Dict[str, bool]:
        """Get summary of validation results"""
        return self.validation_results
    
    def get_cleaning_summary(self) -> List[str]:
        """Get summary of cleaning actions"""
        return self.cleaning_actions


class DataPreprocessor:
    """Preprocess data for forecasting"""
    
    @staticmethod
    def detect_seasonality(
        data: pd.DataFrame,
        freq_list: List[int] = [7, 30, 365]
    ) -> Dict[str, float]:
        """Detect seasonality in the data"""
        try:
            seasonality_scores = {}
            
            for freq in freq_list:
                if len(data) >= freq * 2:
                    # Calculate autocorrelation
                    acf = pd.Series(data['quantity_sold']).autocorr(lag=freq)
                    seasonality_scores[f'{freq}_day'] = acf
            
            return seasonality_scores
            
        except Exception as e:
            logger.error(f"Error detecting seasonality: {str(e)}", exc_info=True)
            return {}
    
    @staticmethod
    def decompose_time_series(
        data: pd.DataFrame
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Decompose time series into trend, seasonal, and residual components"""
        try:
            # Ensure we have enough data
            if len(data) < 14:  # Minimum 2 weeks
                return None, None, None
            
            decomposition = seasonal_decompose(
                data['quantity_sold'],
                period=7,  # Weekly seasonality
                extrapolate_trend='freq'
            )
            
            return (
                decomposition.trend,
                decomposition.seasonal,
                decomposition.resid
            )
            
        except Exception as e:
            logger.error(f"Error decomposing time series: {str(e)}", exc_info=True)
            return None, None, None
    
    @staticmethod
    def calculate_features(
        data: pd.DataFrame
    ) -> pd.DataFrame:
        """Calculate additional features for forecasting"""
        try:
            features = data.copy()
            
            # Time-based features
            features['dayofweek'] = features.index.dayofweek
            features['month'] = features.index.month
            features['quarter'] = features.index.quarter
            features['year'] = features.index.year
            features['dayofyear'] = features.index.dayofyear
            features['weekofyear'] = features.index.isocalendar().week
            
            # Lag features
            for lag in [1, 7, 30]:
                if len(data) > lag:
                    features[f'lag_{lag}'] = features['quantity_sold'].shift(lag)
            
            # Rolling statistics
            for window in [7, 30]:
                if len(data) > window:
                    features[f'rolling_mean_{window}'] = features[
                        'quantity_sold'
                    ].rolling(window=window).mean()
                    features[f'rolling_std_{window}'] = features[
                        'quantity_sold'
                    ].rolling(window=window).std()
            
            return features
            
        except Exception as e:
            logger.error(f"Error calculating features: {str(e)}", exc_info=True)
            return data
