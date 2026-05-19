from datetime import datetime, timedelta

today = datetime.now().strftime('%Y-%m-%d')
yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

print(f'Today: {today}')
print(f'Yesterday: {yesterday}')

def clean_log_file(input_file, output_file):
    count = 0
    try:
        with open(input_file, 'r', encoding='utf-8') as f_in, open(output_file, 'w', encoding='utf-8') as f_out:
            for line in f_in:
                if today in line or yesterday in line:
                    f_out.write(line)
                    count += 1
    except Exception as e:
        print(f'Error processing {input_file}: {e}')
        return 0
    return count

app_file = r'd:\local_pysys\vue-element-plus-admin-master\backend\logs\app.log'
error_file = r'd:\local_pysys\vue-element-plus-admin-master\backend\logs\error.log'

app_count = clean_log_file(app_file, app_file + '.cleaned')
error_count = clean_log_file(error_file, error_file + '.cleaned')

print(f'app.log: {app_count} lines kept')
print(f'error.log: {error_count} lines kept')