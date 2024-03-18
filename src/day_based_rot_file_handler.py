import logging
import os
import datetime


class DayBasedRotatingFileHandler(logging.FileHandler):
    def __init__(self, filename, backup_count=60, *args, **kwargs):
        self.backup_count = backup_count
        self.today = datetime.date.today()
        self.current_log_date = self.today
        self.filename_template = filename
        self.filename = self.get_filename()
        super().__init__(self.filename, *args, **kwargs)

    def emit(self, record):
        """
        Emit a record.

        If the stream was not opened because 'delay' was specified in the
        constructor, open it before calling the superclass's emit.
        """
        if(self.should_rollover(record)):
            self.do_rollover()
        if self.stream is None:
            self.stream = self._open()
        logging.StreamHandler.emit(self, record)

    def should_rollover(self, record):
        return self.current_log_date != datetime.date.today()

    def do_rollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None
        if self.current_log_date != datetime.date.today():
            self.current_log_date = datetime.date.today()
            self.remove_old_log_files()

        self.baseFilename = self.get_filename()
        if not self.delay:
            self.stream = self._open()

    def get_filename(self):
        return self.filename_template.format(date=self.current_log_date)

    def remove_old_log_files(self):
        # Get the current date
        current_date = datetime.date.today()
        log_directory = '/'.join(self.filename.split('/')[0:-1])
        # Calculate the date beyond which log files should be removed
        threshold_date = current_date - datetime.timedelta(days=self.backup_count)

        # Iterate over the files in the log directory
        for filename in os.listdir(log_directory):
            # Check if the file is a log file
            if filename.endswith(".log"):
                # Extract the date from the filename
                date_str = filename.split("_")[1].split(".")[0]
                log_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                # If the log file date is before the threshold date, remove the file
                if log_date <= threshold_date:
                    os.remove(os.path.join(log_directory, filename))