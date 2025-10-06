from datetime import datetime, timedelta

def validate_date_format(date_str):
    """
    Validate that a date string is in YYYY-MM-DD format.
    
    Args:
        date_str (str): Date string to validate
        
    Returns:
        bool: True if valid YYYY-MM-DD format, False otherwise
    """
    try:
        if not date_str or date_str.strip() == '':
            return False
        datetime.strptime(date_str.strip(), '%Y-%m-%d')
        return True
    except ValueError:
        return False

def calculate_next_maintenance(last_maintenance_date, period_weeks, start_date=None):
    """
    Calculate the next maintenance date based on the last maintenance date and period.
    
    Args:
        last_maintenance_date (str): Last maintenance date in 'YYYY-MM-DD' format
        period_weeks (int): Period in weeks
        start_date (str, optional): Start date in 'YYYY-MM-DD' format if no maintenance yet
        
    Returns:
        str: Next maintenance date in 'YYYY-MM-DD' format
    """
    try:
        if not last_maintenance_date or last_maintenance_date == 'Never':
            if start_date:
                return start_date
            return datetime.now().strftime('%Y-%m-%d')
            
        last_date = datetime.strptime(last_maintenance_date, '%Y-%m-%d')
        next_date = last_date + timedelta(weeks=period_weeks)
        return next_date.strftime('%Y-%m-%d')
    except Exception as e:
        print(f"Error calculating next maintenance date: {str(e)}")
        return None

def format_date_for_display(date_str):
    """
    Format date for display. Returns the date in YYYY-MM-DD format.
    
    Args:
        date_str (str): Date in 'YYYY-MM-DD' format
        
    Returns:
        str: Date in 'YYYY-MM-DD' format or 'Never' or 'Invalid Date'
    """
    try:
        if not date_str or date_str == 'Never':
            return 'Never'
            
        # Validate it's already in YYYY-MM-DD format
        datetime.strptime(date_str, '%Y-%m-%d')
        return date_str  # Return exactly as received
    except ValueError:
        print(f"Error: Invalid date format '{date_str}'. Expected YYYY-MM-DD format.")
        return 'Invalid Date'
    except Exception as e:
        print(f"Error formatting date: {str(e)}")
        return 'Invalid Date'

def format_date_for_db(date_str):
    """
    Format date for database storage. Returns the date in YYYY-MM-DD format.
    
    Args:
        date_str (str): Date in 'YYYY-MM-DD' format
        
    Returns:
        str: Date in 'YYYY-MM-DD' format or None if invalid
    """
    try:
        if not date_str or date_str == 'Never':
            return None
            
        # Validate it's in YYYY-MM-DD format
        datetime.strptime(date_str, '%Y-%m-%d')
        return date_str  # Return exactly as received
    except ValueError:
        print(f"Error: Invalid date format '{date_str}' for database. Expected YYYY-MM-DD format.")
        return None
    except Exception as e:
        print(f"Error formatting date for DB: {str(e)}")
        return None

def get_maintenance_status(next_maintenance_date):
    """
    Get the maintenance status based on the next maintenance date.
    
    Args:
        next_maintenance_date (str): Next maintenance date in 'YYYY-MM-DD' format
        
    Returns:
        tuple: (status, color) where status is 'overdue', 'due_soon', or 'on_schedule'
               and color is the corresponding Qt color
    """
    try:
        if not next_maintenance_date:
            return 'on_schedule', None
            
        # Parse the date
        next_date = datetime.strptime(next_maintenance_date, '%Y-%m-%d')
        
        days_until_next = (next_date - datetime.now()).days
        
        if days_until_next < 0:
            return 'overdue', 'red'
        elif days_until_next <= 10:
            return 'due_soon', 'yellow'
        else:
            return 'on_schedule', None
    except Exception as e:
        print(f"Error getting maintenance status: {str(e)}")
        return 'on_schedule', None 