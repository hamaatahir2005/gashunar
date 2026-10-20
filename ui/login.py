"""Native, fully local authentication: sign in and create an account."""
import logging
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QDialog,QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QLabel,QLineEdit,
    QPushButton,QTabWidget,QCheckBox)
from core.paths import resource
from localization.strings import tr


class Login(QDialog):
    def __init__(self,auth,language='ckb',parent=None,allow_signup=True):
        super().__init__(parent)
        self.auth,self.language,self.user=auth,language,None
        self.setup,self.allow_signup=auth.needs_setup(),allow_signup
        self.setWindowTitle('GAS HUNAR — '+tr('Login',language));self.setMinimumWidth(480)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft if language in ('ckb','ar') else Qt.LayoutDirection.LeftToRight)
        layout=QVBoxLayout(self);layout.setContentsMargins(26,22,26,22);layout.setSpacing(14)
        brand_row=QHBoxLayout();logo=QLabel();logo.setFixedSize(70,70)
        logo.setPixmap(QPixmap(str(resource('assets/gas-hunar.png'))).scaled(68,68,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
        brand_row.addWidget(logo);brand=QLabel('GAS HUNAR\nگەس هونەر');brand.setObjectName('brand');brand_row.addWidget(brand);brand_row.addStretch();layout.addLayout(brand_row)
        subtitle=QLabel(self.t('Offline restaurant management'));subtitle.setObjectName('muted');layout.addWidget(subtitle)
        self.message=QLabel();self.message.setObjectName('error');self.message.setWordWrap(True);self.message.hide();layout.addWidget(self.message)
        self.tabs=QTabWidget();self.tabs.setObjectName('authTabs');layout.addWidget(self.tabs)
        login_page=QWidget();login_layout=QVBoxLayout(login_page);login_layout.setContentsMargins(16,18,16,18);login_layout.setSpacing(12)
        heading=QLabel(self.t('Welcome back'));heading.setObjectName('heading');login_layout.addWidget(heading)
        self.username=self.field('Username','login_username')
        self.password=self.field('Password','login_password',secret=True)
        form=QFormLayout();form.addRow(self.t('Username'),self.username);form.addRow(self.t('Password'),self.password);login_layout.addLayout(form)
        show=QCheckBox(self.t('Show password'));show.toggled.connect(lambda checked:self.show_password(self.password,checked));login_layout.addWidget(show)
        self.login_button=QPushButton(self.t('Login'));self.login_button.setObjectName('primary');self.login_button.setAutoDefault(False);self.login_button.clicked.connect(self.submit);login_layout.addWidget(self.login_button)
        self.tabs.addTab(login_page,self.t('Login'))
        self.signup_page=None
        if allow_signup:
            self.signup_page=QWidget();signup_layout=QVBoxLayout(self.signup_page);signup_layout.setContentsMargins(16,18,16,18);signup_layout.setSpacing(12)
            self.signup_heading=QLabel(self.t('Create administrator' if self.setup else 'Create account'));self.signup_heading.setObjectName('heading');signup_layout.addWidget(self.signup_heading)
            self.signup_hint=QLabel();self.signup_hint.setObjectName('muted');self.signup_hint.setWordWrap(True);signup_layout.addWidget(self.signup_hint);self.refresh_hint()
            self.signup_name=self.field('Full name','signup_full_name');self.signup_name.setMaxLength(120)
            self.signup_username=self.field('Username','signup_username');self.signup_username.setMaxLength(80)
            self.signup_password=self.field('Password','signup_password',secret=True)
            self.repeat=self.field('Confirm password','signup_confirmation',secret=True)
            form=QFormLayout()
            for label,widget in [('Full name',self.signup_name),('Username',self.signup_username),('Password',self.signup_password),('Confirm password',self.repeat)]:form.addRow(self.t(label),widget)
            signup_layout.addLayout(form)
            password_hint=QLabel(self.t('Use 10–256 characters. Passwords are case-sensitive.'));password_hint.setObjectName('muted');password_hint.setWordWrap(True);signup_layout.addWidget(password_hint)
            reveal=QCheckBox(self.t('Show password'));reveal.toggled.connect(lambda checked:(self.show_password(self.signup_password,checked),self.show_password(self.repeat,checked)));signup_layout.addWidget(reveal)
            self.signup_button=QPushButton(self.t('Sign up'));self.signup_button.setObjectName('primary');self.signup_button.setAutoDefault(False);self.signup_button.clicked.connect(self.create_account);signup_layout.addWidget(self.signup_button)
            self.tabs.addTab(self.signup_page,self.t('Sign up'));self.repeat.returnPressed.connect(self.create_account)
            self.signup_password.returnPressed.connect(self.repeat.setFocus)
        self.username.returnPressed.connect(self.password.setFocus);self.password.returnPressed.connect(self.submit)
        self.tabs.currentChanged.connect(self.tab_changed)
        self.tabs.setCurrentIndex(1 if self.setup and allow_signup else 0)
        close=QPushButton(self.t('Cancel'));close.setAutoDefault(False);close.clicked.connect(self.reject);layout.addWidget(close)
        offline=QLabel('● '+self.t('Accounts stay on this computer. No internet required.'));offline.setObjectName('muted');offline.setWordWrap(True);layout.addWidget(offline)

    def t(self,text):return tr(text,self.language)
    def field(self,label,name,secret=False):
        widget=QLineEdit();widget.setObjectName(name);widget.setPlaceholderText(self.t(label));widget.setClearButtonEnabled(not secret)
        if secret:widget.setEchoMode(QLineEdit.EchoMode.Password)
        return widget
    @staticmethod
    def show_password(widget,checked):widget.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password)
    def refresh_hint(self):
        self.signup_heading.setText(self.t('Create administrator' if self.setup else 'Create account'))
        self.signup_hint.setText(self.t('The first account manages this restaurant.' if self.setup else 'New accounts have cashier access. Administrative settings and financial reports stay restricted.'))
    def tab_changed(self,index):
        self.message.hide();self.password.clear()
        if self.allow_signup:self.signup_password.clear();self.repeat.clear()
    def feedback(self,text,success=False):
        self.message.setObjectName('offline' if success else 'error');self.message.setText(self.t(text));self.message.show()
        self.message.style().unpolish(self.message);self.message.style().polish(self.message)
    def create_account(self):
        if not self.allow_signup:return
        self.signup_button.setEnabled(False)
        try:
            username=self.signup_username.text().strip()
            self.auth.sign_up(username,self.signup_password.text(),self.repeat.text(),self.signup_name.text())
            self.setup=False;self.refresh_hint();self.tabs.setCurrentIndex(0);self.username.setText(username)
            self.signup_password.clear();self.repeat.clear();self.password.clear();self.password.setFocus()
            self.feedback('Account created. Sign in to continue.',success=True)
        except (ValueError,PermissionError) as exc:self.feedback(str(exc))
        except Exception as exc:
            logging.error('Account registration failed (%s)',type(exc).__name__)
            self.feedback('Could not create account. Please try again.')
        finally:self.signup_button.setEnabled(True)
    def submit(self):
        self.login_button.setEnabled(False)
        try:
            if self.auth.needs_setup():
                if self.allow_signup:self.tabs.setCurrentIndex(1)
                self.feedback('Create the first account using Sign up.');return
            self.user=self.auth.login(self.username.text(),self.password.text());self.password.clear();self.accept()
        except (ValueError,PermissionError) as exc:self.feedback(str(exc));self.password.clear();self.password.setFocus()
        except Exception as exc:
            logging.error('Local sign-in failed (%s)',type(exc).__name__)
            self.feedback('Could not sign in. Please try again.')
        finally:self.login_button.setEnabled(True)
