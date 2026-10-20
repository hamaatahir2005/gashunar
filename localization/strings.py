# Shared source text remains readable English; all primary navigation and checkout labels are translated.
TEXT = {
 'ckb': {'Dashboard':'داشبۆرد','Point of sale':'کاشێر','Products':'بەرهەمەکان','Tables':'مێزەکان','Kitchen':'چێشتخانە','Inventory':'کۆگا','Purchases':'کڕینەکان','Expenses':'خەرجییەکان','Customers':'کڕیارەکان','Employees':'کارمەندان','Reports':'ڕاپۆرتەکان','Settings':'ڕێکخستنەکان','Backups':'پاشەکەوت','Orders':'داواکارییەکان','Search':'گەڕان','Add':'زیادکردن','Edit':'دەستکاری','Save':'پاشەکەوتکردن','Cancel':'هەڵوەشاندنەوە','Name':'ناو','Price':'نرخ','Cost':'تێچوو','Code':'کۆد','Category':'پۆل','Barcode':'بارکۆد','Quantity':'بڕ','Notes':'تێبینی','Total':'کۆی گشتی','Pay':'پارەدان','Hold order':'ڕاگرتنی داواکاری','Cash':'نەقد','Card':'کارت','Login':'چوونەژوورەوە','Username':'ناوی بەکارهێنەر','Password':'وشەی نهێنی','Create administrator':'دروستکردنی بەڕێوەبەر','Logout':'چوونەدەرەوە','Open drawer':'کردنەوەی سندوق','Close drawer':'داخستنی سندوق','Refresh':'نوێکردنەوە','Print':'چاپکردن','Export PDF':'هەناردەی PDF','Export CSV':'هەناردەی CSV','Import CSV':'هاوردەی CSV','Archive':'ئەرشیف','Phone':'ژمارەی تەلەفۆن','Address':'ناونیشان','Language':'زمان','Theme':'ڕووکار','Dark':'تاریک','Light':'ڕوون','Today':'ئەمڕۆ','Net sales':'فرۆشتنی خاوێن','Gross profit':'قازانجی گشتی','Net profit':'قازانجی خاوێن','Cash movement':'گۆڕانی نەقد','Low stock':'کەمیی کۆگا','Pending kitchen':'چاوەڕوانی چێشتخانە','Order count':'ژمارەی داواکاری','Customers served':'کڕیارانی خزمەتکراو','Open tables':'مێزە کراوەکان','Completed':'تەواوکراو','Gross sales':'فرۆشتنی گشتی','Discount':'داشکاندن','Tax':'باج','Service':'خزمەتگوزاری','Confirm':'پەسەندکردن','Receipt':'پسووڵە','Refund':'گەڕاندنەوە','Create backup':'دروستکردنی پاشەکەوت','Restore backup':'گەڕاندنەوەی پاشەکەوت','Available':'بەردەست','Occupied':'گیراو','Reserved':'حجزکراو','Next status':'دۆخی داهاتوو','Preparing':'ئامادەکردن','Ready':'ئامادەیە','New':'نوێ','Add ingredient':'زیادکردنی پێکهاتە','Adjust stock':'ڕێکخستنی کۆگا','Recipe':'ڕێچکە','Add supplier':'زیادکردنی دابینکەر','Purchase':'کڕین','Attendance':'ئامادەبوون','Change password':'گۆڕینی وشەی نهێنی','Full screen':'پڕشاشە','Remove':'سڕینەوە','Resume':'بەردەوامبوون','Unit':'یەکە','Minimum':'کەمترین','Supplier':'دابینکەر','Amount':'بڕی پارە','Date':'بەروار','Description':'وەسف','Method':'شێوازی پارەدان','Capacity':'ژمارەی کەس','Section':'بەش','Status':'دۆخ','Order type':'جۆری داواکاری','Table':'مێز','Customer':'کڕیار','Payment':'پارەدان','Settings saved':'ڕێکخستنەکان پاشەکەوت کران','Error':'هەڵە','Success':'سەرکەوتوو','Empty cart':'سەبەتە بەتاڵە','Welcome':'بەخێربێن'},
 'ar': {'Dashboard':'لوحة التحكم','Point of sale':'نقطة البيع','Products':'المنتجات','Tables':'الطاولات','Kitchen':'المطبخ','Inventory':'المخزون','Purchases':'المشتريات','Expenses':'المصروفات','Customers':'العملاء','Employees':'الموظفون','Reports':'التقارير','Settings':'الإعدادات','Backups':'النسخ الاحتياطي','Orders':'الطلبات','Search':'بحث','Add':'إضافة','Edit':'تعديل','Save':'حفظ','Cancel':'إلغاء','Name':'الاسم','Price':'السعر','Cost':'التكلفة','Quantity':'الكمية','Total':'المجموع','Pay':'دفع','Hold order':'تعليق الطلب','Cash':'نقد','Card':'بطاقة','Login':'دخول','Username':'اسم المستخدم','Password':'كلمة المرور','Create administrator':'إنشاء مدير','Logout':'خروج','Refresh':'تحديث','Print':'طباعة','Phone':'الهاتف','Address':'العنوان','Language':'اللغة','Theme':'المظهر','Net sales':'صافي المبيعات','Gross profit':'مجمل الربح','Net profit':'صافي الربح','Discount':'خصم','Tax':'ضريبة','Service':'خدمة','Receipt':'إيصال','Refund':'استرداد','Status':'الحالة','Date':'التاريخ','Amount':'المبلغ','Description':'الوصف','Customer':'العميل','Table':'الطاولة','Payment':'الدفع','Error':'خطأ','Success':'تم','New':'جديد','Preparing':'قيد التحضير','Ready':'جاهز','Completed':'مكتمل'},
 'en': {}
}


def tr(text, language='ckb'):
    return TEXT.get(language, {}).get(text, text)

# Version 0.2: reporting, product-photo forms, themes and printer controls.
TEXT['ckb'].update({
 'Financial overview':'پوختەی دارایی','Your restaurant, at a glance':'چێشتخانەکەت لە یەک نیگادا',
 'Profit = revenue − food cost − expenses':'قازانج = داهات − تێچووی خواردن − خەرجی',
 'From date':'لە بەرواری','To date':'تا بەرواری','This week':'ئەم هەفتەیە','This month':'ئەم مانگە',
 'Calculate':'حیسابکردن','Both dates included · Iraq time · Week starts Saturday':'هەردوو بەروارەکە دەژمێردرێن · کاتی عێراق · دەستپێکی هەفتە: شەممە',
 'Day profit':'قازانجی ڕۆژ','Week profit':'قازانجی هەفتە','Month profit':'قازانجی مانگ',
 'Period cards follow the selected end date':'قازانجی ڕۆژ و هەفتە و مانگ بەپێی بەرواری کۆتایی هەڵبژێردراوە',
 'Cost of goods':'تێچووی خواردن','Daily net profit':'قازانجی خاوێنی ڕۆژانە','Best sellers':'پڕفرۆشترین بەرهەمەکان',
 'Export complete':'هەناردەکردن تەواو بوو','Start date must not be after end date':'بەرواری دەستپێک نابێت دوای بەرواری کۆتایی بێت',
 'Add product':'زیادکردنی بەرهەم','Edit product':'دەستکاری بەرهەم','Save product':'پاشەکەوتکردنی بەرهەم',
 'Image':'وێنە','Product photo':'وێنەی بەرهەم','Upload image':'بارکردنی وێنە','Archived':'ئەرشیفکراو',
 'Local PNG / JPEG / WebP · up to 15 MB':'وێنەی ناوخۆ PNG / JPEG / WebP · تا ١٥ مێگابایت',
 'Archive selected product?':'بەرهەمی هەڵبژێردراو ئەرشیف بکرێت؟','Workspace':'بەشی کار',
 'Offline':'بێ ئینتەرنێت','Appearance':'ڕووکار','Receipt printer':'پرێنتەری وەسڵ','Paper width':'پانی کاغەز',
 'Print preview':'پێشبینینی چاپ','Save PDF':'پاشەکەوتکردنی PDF','No printers installed':'هیچ پرێنتەرێک دانەمەزراوە',
 'Install a Windows printer to print. PDF export is still available.':'بۆ چاپکردن پرێنتەرێک لە Windows دابمەزرێنە. هەناردەی PDF بەردەستە.',
 'Printer preferences saved':'هەڵبژاردەکانی پرێنتەر پاشەکەوت کران','Balance due':'پارەی ماوە',
 'takeaway':'بردنەوە','dine-in':'ناو چێشتخانە','delivery':'گەیاندن','new':'نوێ','preparing':'لە ئامادەکردندایە','ready':'ئامادەیە','completed':'تەواوکراو','confirmed':'پەسەندکراو','held':'ڕاگیراو','refunded':'گەڕێندراوە','cancelled':'هەڵوەشێندراوە',
})
TEXT['ar'].update({
 'Financial overview':'نظرة مالية','Your restaurant, at a glance':'مطعمك في لمحة','Profit = revenue − food cost − expenses':'الربح = الإيراد − تكلفة الطعام − المصروفات',
 'From date':'من تاريخ','To date':'إلى تاريخ','This week':'هذا الأسبوع','This month':'هذا الشهر','Today':'اليوم','Calculate':'احسب',
 'Both dates included · Iraq time · Week starts Saturday':'التاريخان مشمولان · توقيت العراق · يبدأ الأسبوع السبت',
 'Day profit':'ربح اليوم','Week profit':'ربح الأسبوع','Month profit':'ربح الشهر','Period cards follow the selected end date':'تعتمد الفترات على تاريخ النهاية المحدد',
 'Cost of goods':'تكلفة الطعام','Daily net profit':'صافي الربح اليومي','Best sellers':'الأكثر مبيعاً','Export complete':'تم التصدير',
 'Start date must not be after end date':'يجب ألا يتجاوز تاريخ البداية تاريخ النهاية','Add product':'إضافة منتج','Edit product':'تعديل المنتج','Save product':'حفظ المنتج',
 'Image':'الصورة','Product photo':'صورة المنتج','Upload image':'رفع صورة','Archived':'مؤرشف','Local PNG / JPEG / WebP · up to 15 MB':'صورة محلية PNG / JPEG / WebP · حتى 15 ميغابايت',
 'Archive selected product?':'أرشفة المنتج المحدد؟','Workspace':'مساحة العمل','Offline':'غير متصل','Appearance':'المظهر','Dark':'داكن','Light':'فاتح',
 'Receipt printer':'طابعة الإيصالات','Paper width':'عرض الورق','Print preview':'معاينة الطباعة','Save PDF':'حفظ PDF','No printers installed':'لا توجد طابعات مثبتة',
 'Install a Windows printer to print. PDF export is still available.':'ثبّت طابعة في Windows للطباعة. يمكنك تصدير PDF.',
 'Printer preferences saved':'تم حفظ إعدادات الطابعة','Balance due':'الرصيد المستحق',
 'takeaway':'سفري','dine-in':'داخل المطعم','delivery':'توصيل','new':'جديد','preparing':'قيد التحضير','ready':'جاهز','completed':'مكتمل','confirmed':'مؤكد','held':'معلق','refunded':'مسترد','cancelled':'ملغى',
})

# Version 0.3: offline sign-up and sign-in.
TEXT['ckb'].update({
 'Sign up':'دروستکردنی ئەکاونت','Create account':'ئەکاونتێک دروست بکە','Full name':'ناوی تەواو',
 'Confirm password':'دووبارەکردنەوەی وشەی نهێنی','Show password':'پیشاندانی وشەی نهێنی',
 'Welcome back':'بەخێربێیتەوە','Offline restaurant management':'بەڕێوەبردنی چێشتخانە بەبێ ئینتەرنێت',
 'Use 10–256 characters. Passwords are case-sensitive.':'وشەی نهێنی لە ١٠ تا ٢٥٦ پیت بێت. پیتی گەورە و بچووک جیاوازن.',
 'Accounts stay on this computer. No internet required.':'ئەکاونتەکان لەسەر ئەم کۆمپیوتەرە دەمێننەوە. پێویست بە ئینتەرنێت نییە.',
 'The first account manages this restaurant.':'یەکەم ئەکاونت بەڕێوەبەری ئەم چێشتخانەیە دەبێت.',
 'New accounts have cashier access. Administrative settings and financial reports stay restricted.':'ئەکاونتی نوێ دەسەڵاتی کاشێری دەبێت. ڕێکخستنەکانی بەڕێوەبەر و ڕاپۆرتە داراییەکان سنووردارن.',
 'Account created. Sign in to continue.':'ئەکاونتەکە دروست کرا. بۆ بەردەوامبوون بچۆ ژوورەوە.',
 'Create the first account using Sign up.':'یەکەم ئەکاونت لە بەشی دروستکردنی ئەکاونت دروست بکە.',
 'Passwords do not match':'وشە نهێنییەکان یەکسان نین',
 'Password must contain 10–256 characters':'وشەی نهێنی دەبێت لە ١٠ تا ٢٥٦ پیت بێت',
 'Enter a username (maximum 80 characters)':'ناوی بەکارهێنەر بنووسە؛ زۆرترین ٨٠ پیت',
 'Enter a name (maximum 120 characters)':'ناوێک بنووسە؛ زۆرترین ١٢٠ پیت',
 'This username is already taken':'ئەم ناوی بەکارهێنەرە پێشتر بەکارهاتووە',
 'Invalid credentials or account temporarily locked':'زانیارییەکان هەڵەن یان ئەکاونتەکە بۆ ماوەیەک داخراوە',
 'Could not create account. Please try again.':'ئەکاونتەکە دروست نەکرا. تکایە دووبارە هەوڵ بدەوە.',
 'Could not sign in. Please try again.':'چوونەژوورەوە سەرکەوتوو نەبوو. تکایە دووبارە هەوڵ بدەوە.',
})
TEXT['ar'].update({
 'Sign up':'إنشاء حساب','Create account':'أنشئ حساباً','Full name':'الاسم الكامل','Confirm password':'تأكيد كلمة المرور',
 'Show password':'إظهار كلمة المرور','Welcome back':'مرحباً بعودتك','Offline restaurant management':'إدارة المطعم دون إنترنت',
 'Use 10–256 characters. Passwords are case-sensitive.':'استخدم 10–256 حرفاً. كلمات المرور حساسة لحالة الأحرف.',
 'Accounts stay on this computer. No internet required.':'تُحفظ الحسابات على هذا الكمبيوتر. لا تحتاج إلى الإنترنت.',
 'The first account manages this restaurant.':'الحساب الأول هو مدير هذا المطعم.',
 'New accounts have cashier access. Administrative settings and financial reports stay restricted.':'الحسابات الجديدة لها صلاحيات الكاشير. تبقى الإعدادات الإدارية والتقارير المالية مقيدة.',
 'Account created. Sign in to continue.':'تم إنشاء الحساب. سجّل الدخول للمتابعة.',
 'Create the first account using Sign up.':'أنشئ الحساب الأول من صفحة إنشاء حساب.',
 'Passwords do not match':'كلمتا المرور غير متطابقتين','Password must contain 10–256 characters':'يجب أن تتكون كلمة المرور من 10–256 حرفاً',
 'Enter a username (maximum 80 characters)':'أدخل اسم مستخدم بحد أقصى 80 حرفاً',
 'Enter a name (maximum 120 characters)':'أدخل اسماً بحد أقصى 120 حرفاً','This username is already taken':'اسم المستخدم هذا مستخدم بالفعل',
 'Invalid credentials or account temporarily locked':'بيانات الدخول غير صحيحة أو الحساب مقفل مؤقتاً',
 'Could not create account. Please try again.':'تعذر إنشاء الحساب. حاول مرة أخرى.','Could not sign in. Please try again.':'تعذر تسجيل الدخول. حاول مرة أخرى.',
})
