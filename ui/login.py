from PySide6.QtWidgets import QDialog,QVBoxLayout,QLabel,QLineEdit,QPushButton,QMessageBox
from localization.strings import tr


class Login(QDialog):
    def __init__(self,auth,language='ckb',parent=None):
        super().__init__(parent);self.auth,self.language,self.user=auth,language,None
        self.setWindowTitle('GAS HUNAR — گەس هونەر');self.setMinimumWidth(430)
        layout=QVBoxLayout(self);brand=QLabel('GAS HUNAR\nگەس هونەر');brand.setObjectName('brand');layout.addWidget(brand)
        self.setup=auth.needs_setup();title='Create administrator' if self.setup else 'Login';layout.addWidget(QLabel(tr(title,language)))
        self.username=QLineEdit();self.username.setPlaceholderText(tr('Username',language));self.password=QLineEdit();self.password.setPlaceholderText(tr('Password',language));self.password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.username);layout.addWidget(self.password)
        if self.setup:
            self.repeat=QLineEdit();self.repeat.setEchoMode(QLineEdit.EchoMode.Password);self.repeat.setPlaceholderText('Confirm password • 10+ characters');layout.addWidget(self.repeat)
        button=QPushButton(tr(title,language));button.setObjectName('primary');button.clicked.connect(self.submit);layout.addWidget(button);self.password.returnPressed.connect(self.submit)
    def submit(self):
        try:
            if self.setup:
                if self.password.text()!=self.repeat.text():raise ValueError('Passwords do not match')
                self.auth.setup(self.username.text(),self.password.text());self.setup=False
            self.user=self.auth.login(self.username.text(),self.password.text());self.accept()
        except Exception as exc:QMessageBox.warning(self,tr('Error',self.language),str(exc))
