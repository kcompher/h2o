import unittest, time, sys
sys.path.extend(['.','..','py'])
import h2o, h2o_cmd, h2o_glm, h2o_hosts, h2o_import as h2i, h2o_jobs, h2o_gbm

DO_CLASSIFICATION = True

def showResults(GBMResult, expectedError):
    print "GBMResult:", h2o.dump_json(GBMResult)
    jobs = GBMResult['jobs']        
    for jobnum, j in enumerate(jobs):
        _distribution = j['_distribution'] 
        model_key = j['destination_key']
        job_key = j['job_key']
        inspect = h2o_cmd.runInspect(key=model_key)
        # print "jobnum:", jobnum, h2o.dump_json(inspect)
        gbmTrainView = h2o_cmd.runGBMView(model_key=model_key)
        print "jobnum:", jobnum, h2o.dump_json(gbmTrainView)

        if DO_CLASSIFICATION:
            cm = gbmTrainView['gbm_model']['cm']
            pctWrongTrain = h2o_gbm.pp_cm_summary(cm);
            if pctWrongTrain > expectedError:
                raise Exception("Should have < %s error here. pctWrongTrain: %s" % expectedError, pctWrongTrain)

            errsLast = gbmTrainView['gbm_model']['errs'][-1]
            print "\nTrain", jobnum, job_key, "\n==========\n", "pctWrongTrain:", pctWrongTrain, "errsLast:", errsLast
            print "GBM 'errsLast'", errsLast
            print h2o_gbm.pp_cm(cm)
        else:
            print "\nTrain", jobnum, job_key, "\n==========\n", "errsLast:", errsLast
            print "GBMTrainView errs:", gbmTrainView['gbm_model']['errs']


class Basic(unittest.TestCase):
    def tearDown(self):
        h2o.check_sandbox_for_errors()

    @classmethod
    def setUpClass(cls):
        global localhost
        localhost = h2o.decide_if_localhost()
        if (localhost):
            h2o.build_cloud(1)
        else:
            h2o_hosts.build_cloud_with_hosts(1)

    @classmethod
    def tearDownClass(cls):
        h2o.tear_down_cloud()

    def test_GBMGrid_basic_benign(self):
        csvFilename = "benign.csv"
        print "\nStarting", csvFilename 
        csvPathname = 'logreg/' + csvFilename
        parseResult = h2i.import_parse(bucket='smalldata', path=csvPathname, hex_key=csvFilename + ".hex", schema='put')
        # columns start at 0
        # cols 0-13. 3 is output
        # no member id in this one
        
        # check the first in the models list. It should be the best
        colNames = [ 'STR','OBS','AGMT','FNDX','HIGD','DEG','CHK', 'AGP1','AGMN','NLV','LIV','WT','AGLP','MST' ]
        modelKey = 'GBMGrid_benign'

        # 'cols', 'ignored_cols_by_name', and 'ignored_cols' have to be exclusive
        params = {
            'destination_key': modelKey,
            'ignored_cols_by_name': 'STR',
            'learn_rate': '.1,.2',
            'ntrees': '3,4',
            'max_depth': '5,7',
            'min_rows': '1,2',
            'response': 'FNDX',
            'classification': 1 if DO_CLASSIFICATION else 0,
            }

        kwargs = params.copy()
        timeoutSecs = 1800
        start = time.time()
        GBMResult = h2o_cmd.runGBM(parseResult=parseResult, **kwargs)
        elapsed = time.time() - start
        print "GBM training completed in", elapsed, "seconds."
        showResults(GBMResult, 0)

    def test_GBMGrid_basic_prostate(self):
        csvFilename = "prostate.csv"
        print "\nStarting", csvFilename
        # columns start at 0
        csvPathname = 'logreg/' + csvFilename
        parseResult = h2i.import_parse(bucket='smalldata', path=csvPathname, hex_key=csvFilename + ".hex", schema='put')
        colNames = ['ID','CAPSULE','AGE','RACE','DPROS','DCAPS','PSA','VOL','GLEASON']

        modelKey = 'GBMGrid_prostate'
        # 'cols', 'ignored_cols_by_name', and 'ignored_cols' have to be exclusive
        params = {
            'destination_key': modelKey,
            'ignored_cols_by_name': 'ID',
            'learn_rate': '.1,.2',
            'ntrees': '1,2',
            'max_depth': '8,9',
            'min_rows': '1,5',
            'response': 'CAPSULE',
            'classification': 1 if DO_CLASSIFICATION else 0,
            }

        kwargs = params.copy()
        timeoutSecs = 1800
        start = time.time()
        GBMResult = h2o_cmd.runGBM(parseResult=parseResult, **kwargs)
        elapsed = time.time() - start
        print "GBM training completed in", elapsed, "seconds."
        showResults(GBMResult, 10)


if __name__ == '__main__':
    h2o.unit_main()
