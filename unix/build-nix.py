import json
import os
import time
import platform
from config import *
from local_env import *


""" Call Linux build machine to generate builds """
if platform.system() == 'Darwin' and callLinuxBuildMachine == 1:
	os.system('ssh '+ userName +'@'+ ipAddr +' "cd '+ buildCode +' && python3 build-nix.py"')


""" Pre build checks """

""" Check file exists, Check if not empty, Read version file(postgres_versions.json) """

try:
	if os.path.isfile('postgres_versions.json') != True:
		print('postgres_versions.json file not found ...')
		exit()

	if os.path.getsize('postgres_versions.json') == 0:
		print('postgres_versions.json should not be an empty file ...')
		exit()

	with open('postgres_versions.json', 'r') as componentsInfo:
		componentsInfo = json.load(componentsInfo)

except:
	print('Please use proper formatting for postgres_versions.json file ...')

""" Check share lib folder available or not on give path """

if os.path.exists(shareLib) and os.path.isdir(shareLib):
	if not os.listdir(shareLib):
		print('Provided share lib is empty ...')
		exit()
else:
	print('provided share lib don"t exists ...')
	exit()

print('Pre build checks are executed successfully ...')


""" Checking operating system and setting platform related commands """
DOWNLOAD_KEY = 'curl -O'
osType = platform.system();
if osType == 'Linux':
	DOWNLOAD_KEY = 'wget'


""" Generate build """

print('Preparing to generate builds now ...')

""" Reading postgreSQ versions from postgres_versions.json """

with open('postgres_versions.json', 'r') as postgresVersions:
	postgresVersions = json.load(postgresVersions)


""" Saving current state of PATH """
PATH = os.environ['PATH']


for postgresVersion in postgresVersions:

	""" Setting up system PATH variables
        This section will hold/set/modify all the build related PATHS """

	print('Setting up proper system PATH variables ...')
	os.environ['LD_LIBRARY_PATH']   = shareLib +'/lib'
	os.environ['CPPFLAGS']          = '-I'+ shareLib +'/include'
	os.environ['LDFLAGS']           = ' -L'+ shareLib +'/lib'


	dateTime = time.strftime("%Y%m%d%H%M%S")

	print('\nStarting build process for '+ postgresVersion['fullVersion'])

	print('\n\nSetting up work dir structure ...')

	currentProjectDir = root +'/workDir/'+ projectName
	currentBuild = currentProjectDir +'/'+ dateTime +'/'+ postgresVersion['fullVersion']

	sourceDir = currentBuild +'/'+ 'source'
	logsDir = currentBuild +'/'+ 'logs'
	buildDir = currentBuild +'/'+ 'build' +'/'+ postgresVersion['majorVersion']

	res = os.system('mkdir -p '+ sourceDir +' && echo '+ sourceDir)
	res = os.system('mkdir -p '+ logsDir   +' && echo '+ logsDir)
	res = os.system('mkdir -p '+ buildDir  +' && echo '+ buildDir)
	if res != 0:
		print('\nCould not able to create proper work dir exit code 1 ...')
		exit()

	time.sleep(1)

	""" Setting system PATH to its default state first then set it to current build this is because if we have to built more than 1 postgreSQL versions then PATH will contain project dir PATH or each build which is why we need to remove the PATH of old builds first same case is true of build dir as we need to add current build dir path in LDfLAGS """

	os.environ['PATH']              = PATH

	os.environ['LDFLAGS']           = '-Wl,-rpath,'+ buildDir + os.environ['LDFLAGS'] 

	os.environ['PATH']              = buildDir +"/bin:"+ shareLib +"/bin:"+ os.environ['PATH']


	print('Downloading PostgreSQL source code ...')
	res = os.system('cd '+ sourceDir +' && '+ DOWNLOAD_KEY +' '+ postgresVersion['tarball'] +' > '+ logsDir +'/postgreSQL-source.log 2>&1')
	if res != 0:
		print('\nSomething went wrong for PostgreSQL source code downloading please refer to postgreSQL-source.log file ...')
		exit()


	""" Unzip the source code """
	print('Uncompress the source code ...')
	res = os.system('cd '+ sourceDir +' && tar xzf postgresql-'+ postgresVersion['fullVersion'] +'.tar.gz')
	if res != 0:
		print('\nSomething went wrong with PostgreSQL source code uncompressing ...')
		exit()


	""" Running ./configure on PostgreSQL """
	print('Running ./configure ...')
	
	""" Creating configure options """
	configureWith = ''
	configureFlags = ''

	if postgresVersion['OPENSSL'] == '1':
		configureWith += ' --with-openssl '
		os.environ['OPENSSL_HOME']      = openssl_home
		os.environ['LD_LIBRARY_PATH']   = os.environ['OPENSSL_HOME'] +'/lib:'+ os.environ['LD_LIBRARY_PATH']
		os.environ['CPPFLAGS']          = '-I'+ os.environ['OPENSSL_HOME'] +'/include '+ os.environ['CPPFLAGS']
		os.environ['LDFLAGS']           = os.environ['LDFLAGS'] +' -L'+ os.environ['OPENSSL_HOME'] +"/lib"
		os.environ['PATH']              = os.environ['OPENSSL_HOME'] +"/bin:"+ os.environ['PATH']

	if postgresVersion['GSSAPI']  == '1':
		configureWith += ' --with-gssapi '

	if postgresVersion['PYTHON']  == '1':
		configureWith += ' --with-python '
		os.environ['PYTHON_HOME']       = python_home
		os.environ['LD_LIBRARY_PATH']   = os.environ['PYTHON_HOME'] +'/lib:'+ os.environ['LD_LIBRARY_PATH']
		os.environ['PYTHON']            = os.environ['PYTHON_HOME'] +'/bin/python3'
		os.environ['CPPFLAGS']          = '-I'+ os.environ['PYTHON_HOME'] +'/inlclude/python3.4m '+ os.environ['CPPFLAGS']
		os.environ['LDFLAGS']           = os.environ['LDFLAGS'] +' -L'+ os.environ['PYTHON_HOME'] +'/lib'
		os.environ['PATH']              = os.environ['PYTHON_HOME'] +"/bin:"+ os.environ['PATH']

	if postgresVersion['PERL']    == '1':
		configureWith += ' --with-perl '
		os.environ['LD_LIBRARY_PATH']   = pl_languages +'/Perl-5.26/lib:'+ os.environ['LD_LIBRARY_PATH']
		os.environ['LDFLAGS']           = os.environ['LDFLAGS'] +' -L'+ pl_languages +'/Perl-5.26/lib'
		os.environ['PATH']              = pl_languages +'/Perl-5.26/bin:'+ os.environ['PATH']

	if postgresVersion['LDAP']    == '1':
		configureWith += ' --with-ldap '

	if postgresVersion['ZLIB']    == '1':
		configureWith += ' --with-zlib '

	if postgresVersion['TCL']     == '1':
		configureWith += ' --with-tcl --with-tclconfig='+ pl_languages +'/Tcl-8.6/lib '
		os.environ['TCLSH'] = pl_languages +"/Tcl-8.6/lib"

	if postgresVersion['ICU']     == '1':
		configureWith += ' --with-icu '
		configureFlags = ' ICU_CFLAGS=\'-I'+ shareLib +'/include\' ICU_LIBS=\'-L'+ shareLib +'/lib -licui18n -licuuc -licudata\' '

	""" Executing ./configure command now """
	print('./configure '+ configureWith)
	res = os.system('cd '+ sourceDir +'/postgresql-'+ postgresVersion['fullVersion'] +' && ./configure '+ configureWith +' '+ configureFlags +' --prefix='+ buildDir +' > '+ logsDir +'/postgreSQL-configure.log 2>&1')
	if res != 0:
		print('\nSomething went wrong with ./configure see\n'+ logsDir +'/postgreSQL-configure.log ...')
		exit()


	""" Running make on PostgreSQL source code """
	print('Running make ...')
	res = os.system('cd '+ sourceDir +'/postgresql-'+ postgresVersion['fullVersion'] +' && make > '+ logsDir +'/postgreSQL-make.log 2>&1')
	if res != 0:
		print('\nSomething went wrong with make see\n'+ logsDir +'/postgreSQL-make.log ...')
		exit()


	""" Running make check on PostgreSQL """	
	print('Running make check ...')
	res = os.system('cd '+ sourceDir +'/postgresql-'+ postgresVersion['fullVersion'] +' && make check > '+ logsDir +'/postgreSQL-make-check.log 2>&1')
	if res != 0:
		print('\nSomething went wrong with make check see\n'+ logsDir +'/postgreSQL-make-check.log ...')
		exit()


	""" Running make install on PostgreSQL """
	print('Running make install ...')
	res = os.system('cd '+ sourceDir +'/postgresql-'+ postgresVersion['fullVersion'] +' && make install > '+ logsDir +'/postgreSQL-make-install.log 2>&1')
	if res != 0:
		print('\nSomething went wrong with make install see\n'+ logsDir +'/postgreSQL-make-install.log ...')
		exit()


	if postgresVersion['POSTGIS'] == '1':
		print('\n\nBuild POSTGIS now ...')

		""" Download source code """
		res = os.system('cd '+ sourceDir +' && '+ DOWNLOAD_KEY +' '+ postgresVersion['POSTGISTARBALL'] +' > '+ logsDir +'/postgis-source.log 2>&1')
		if res != 0:
			print('\nSomething went wrong with downloading the source code see\n'+ logsDir +'/postgis-source.log')
			exit()


		""" Uncompress the source code """
		print('Uncompress the source code ...')
		res = os.system('cd '+ sourceDir +' && tar xzf postgis-'+ postgresVersion['POSTGISVERSION'] +'.tar.gz')
		if res != 0:
			print('Something went wrong with postgis uncompressing ...')
			exit()


		""" Running ./configure """
		print('Running ./configure ...')
		res = os.system('cd '+ sourceDir +'/postgis-'+ postgresVersion['POSTGISVERSION'] +' && ./configure --prefix='+ shareLib +' --with-pgconfig='+ buildDir +'/bin/pg_config --with-gdalconfig=' + shareLib + '/bin/gdal-config  --with-geosconfig='+ shareLib +'/bin/geos-config --with-projdir='+ shareLib +' --with-xml2config='+ shareLib +'/bin/xml2-config > '+ logsDir +'/postgis-configure.log 2>&1')
		if res != 0:
			print('\nSomthing went wrong with postgis configure see\n'+ logsDir +'/postgis-configure.log ...')
			exit()


		""" Running make """
		print('Running make ...')
		res = os.system('cd '+ sourceDir +'/postgis-'+ postgresVersion['POSTGISVERSION'] +' && make > '+ logsDir +'/postgis-make.log 2>&1')
		if res != 0:
			print('\nSomething went wrong with make see\n'+ logsDir +'\postgis-make.log ...')
			exit()


		""" Running regression tests on postgis """
		print('Running make check ...')
		
		""" initializing the data dir """
		res = os.system('cd '+ buildDir +'/bin && ./initdb -D '+ logsDir +'/data > '+ logsDir +'/postgreSQL-init.log 2>&1')
		if res != 0:
			print('\nCould not able to initialize the data dir see\n'+ logsDir +'/postgreSQL-init.log ...')
			exit()

		""" Starting postgreSQL server """
		res = os.system('cd '+ buildDir +'/bin && ./pg_ctl -D '+ logsDir +'/data start > '+ logsDir +'/postgreSQL-pgctl.log 2>&1')
		if res != 0:
			print('\nCould not able to start PostgreSQL server see\n'+ logsDir +'/postgreSQL-pgctl.log ...')
			exit()

		""" Running make check on postgis now """
		res = os.system('cd '+ sourceDir +'/postgis-'+ postgresVersion['POSTGISVERSION'] +' && make check > '+ logsDir +'/postgis-make-check.log 2>&1')
		if res != 0:
			print('\nSomething went wrong with make check see\n'+ logsDir +'/postgis-make-check.log ...')
			exit()


		""" running make install on postgis """
		print('Running make install ...')
		res = os.system('cd '+ sourceDir +'/postgis-'+ postgresVersion['POSTGISVERSION'] +' && make install > '+ logsDir +'/postgis-make-install.log 2>&1')
		if res != 0:
			print('\nSomething went wrong with make install see\n'+ logsDir +'/postgis-make-install.lo ...')
			exit()


	""" ****** POST BUILD STEPS ***** """
	print('****** POST BUILD STEPS *****')
	
	""" Copy shareLib/lib into buildDir/lib """
	print('Copy shareLib/lib into buildDir/lib ...')
	os.system('cp -rv '+ shareLib +'/lib/* '+ buildDir +'/lib/')

	""" Copy shareLib/share/gdal into buildDir/share """
	print('Copy shareLib/share/gdal into buildDir/share ...')
	os.system('cp -rv '+ shareLib +'/share/gdal '+ buildDir +'/share/')

	""" Copy sharelib/share/proj from buildDir/share """
	os.system('cp -rv '+ shareLib +'/share/proj '+ buildDir +'/share/')

	""" Copy openssl/lib into buildDir/lib """
	os.system('cp -rv '+ openssl_home +'/lib/* '+ buildDir +'/lib/')

	""" Platform related actions """
	if osType == 'Linux':
		
		""" Setting runtime paths """

		print('Setting runtime paths for bin ...')
		for file in os.listdir(buildDir +'/bin'):
			os.system('cd '+ buildDir +'/bin && chrpath -r "\${ORIGIN}/../lib/" ./'+ file +" >> "+ logsDir +"/postgreSQL-bin-rpaths.log 2>&1")

		print('Setting runtime paths for lib ...')
                for file in os.listdir(buildDir +'/lib'):
                        os.system('cd '+ buildDir +'/lib && chrpath -r "\${ORIGIN}/../lib/" ./'+ file +" >> "+ logsDir +"/postgreSQL-lib-rpaths.log 2>&1")

		if os.path.exists(buildDir +'/lib/postgresql'):
			print('Setting runtime paths for lib/postgresql ...')
        	        for file in os.listdir(buildDir +'/lib/postgresql'):
                	        os.system('cd '+ buildDir +'/lib/postgresql && chrpath -r "\${ORIGIN}/../lib/" ./'+ file +" >> "+ logsDir +"/postgreSQL-postgresql-rpaths.log 2>&1")

		# Uncommit it if we have build a new version of TCL 
                # os.system('cd /opt/2ndQuadrant/pl-languages/Tcl-8.6/bin && chrpath -r "\${ORIGIN}/../lib/" ./tclsh8.6' " >> "+ dir_logs +"/postgreSQL_postgress_rpaths.log 2>&1")
