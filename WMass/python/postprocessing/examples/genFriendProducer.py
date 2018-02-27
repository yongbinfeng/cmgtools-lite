import ROOT
import os, array
import numpy as np
ROOT.PyConfig.IgnoreCommandLineOptions = True

from CMGTools.WMass.postprocessing.framework.datamodel import Collection 
from CMGTools.WMass.postprocessing.framework.eventloop import Module
from PhysicsTools.HeppyCore.utils.deltar import deltaPhi
from math import *

class SimpleVBoson:
    def __init__(self,legs):
        self.legs = legs
        if len(legs)<2:
            print "ERROR: making a VBoson w/ < 2 legs!"
        self.pt1 = legs[0].Pt()
        self.pt2 = legs[1].Pt()
        self.dphi = self.legs[0].Phi()-self.legs[1].Phi()
        self.deta = self.legs[0].Eta()-self.legs[1].Eta()
        self.px1 = legs[0].Px(); self.py1 = legs[0].Py();
        self.px2 = legs[1].Px(); self.py2 = legs[1].Py();
    def pt(self):
        return (self.legs[0]+self.legs[1]).Pt()
    def y(self):
        return (self.legs[0]+self.legs[1]).Rapidity()
    def mt(self):
        return sqrt(2*self.pt1*self.pt2*(1-cos(self.dphi)))
    def ux(self):
        return (-self.px1-self.px2)
    def uy(self):
        return (-self.py1-self.py2)    
    def mll(self):
        return sqrt(2*self.pt1*self.pt2*(cosh(self.deta)-cos(self.dphi)))

class KinematicVars:
    def __init__(self,beamE=6500):
        self.beamE = beamE
    def CSFrame(self,dilepton):
        pMass = 0.938272
        sign = np.sign(dilepton.Z())
        proton1 = ROOT.TLorentzVector(0.,0.,sign*self.beamE,hypot(self.beamE,pMass));  proton2 = ROOT.TLorentzVector(0.,0.,-sign*self.beamE,hypot(self.beamE,pMass))
        proton1.Boost(-dilepton.BoostVector()); proton2.Boost(-dilepton.BoostVector())
        CSAxis = (proton1.Vect().Unit()-proton2.Vect().Unit()).Unit()
        yAxis = (proton1.Vect().Unit()).Cross((proton2.Vect().Unit()));
        yAxis = yAxis.Unit();
        xAxis = yAxis.Cross(CSAxis);
        xAxis = xAxis.Unit();
        return (xAxis,yAxis,CSAxis)
    def cosThetaCS(self,lplus,lminus):
        dilep = lplus + lminus
        boostedLep = ROOT.TLorentzVector(lminus)
        boostedLep.Boost(-dilep.BoostVector())
        csframe = self.CSFrame(dilep)
        return cos(boostedLep.Angle(csframe[2]))
    def cosThetaCM(self,lplus,lminus):
        dilep = lplus + lminus
        boostedLep = ROOT.TLorentzVector(lminus)
        boostedLep.Boost(-dilep.BoostVector())
        modw = sqrt(dilep.X()*dilep.X() + dilep.Y()*dilep.Y() + dilep.Z()*dilep.Z())
        modm = sqrt(boostedLep.X()*boostedLep.X() + boostedLep.Y()*boostedLep.Y() + boostedLep.Z()*boostedLep.Z())
        cos = (dilep.X()*boostedLep.X() + dilep.Y()*boostedLep.Y() + dilep.Z()*boostedLep.Z())/modw/modm
        return cos
    def phiCS(self,lplus,lminus):
        dilep = lplus + lminus
        boostedLep = ROOT.TLorentzVector(lminus)
        boostedLep.Boost(-dilep.BoostVector())
        csframe = self.CSFrame(dilep)
        phi = atan2((boostedLep.Vect()*csframe[1]),(boostedLep.Vect()*csframe[0]))
        if(phi<0): return phi + 2*ROOT.TMath.Pi()
        else: return phi

class GenQEDJetProducer(Module):
    def __init__(self,deltaR,beamEn=7000.):
        self.beamEn=beamEn
        self.deltaR = deltaR
        self.vars = ("pt","eta","phi","mass","pdgId")
        self.genwvars = ("charge","pt","eta","phi","mass","mt","y","costcs","phics","costcm","decayId")
        if "genQEDJetHelper_cc.so" not in ROOT.gSystem.GetLibraries():
            print "Load C++ Worker"
            ROOT.gROOT.ProcessLine(".L %s/src/CMGTools/WMass/python/postprocessing/helpers/genQEDJetHelper.cc+" % os.environ['CMSSW_BASE'])
        else:
            print "genQEDJetHelper_cc.so found in ROOT libraries"
        self._worker = ROOT.GenQEDJetHelper(deltaR)
        self.pdfWeightOffset = 10 #index of first mc replica weight (careful, this should not be the nominal weight, which is repeated in some mc samples).  The majority of run2 LO madgraph_aMC@NLO samples with 5fs matrix element and pdf would use index 10, corresponding to pdf set 263001, the first alternate mc replica for the nominal pdf set 263000 used for these samples
        self.nMCReplicasWeights = 100 #number of input weights (100 for NNPDF 3.0)
        self.nHessianWeights = 60 #number of output weights
        if "PDFWeightsHelper_cc.so" not in ROOT.gSystem.GetLibraries():
            ROOT.gROOT.ProcessLine(".include /cvmfs/cms.cern.ch/slc6_amd64_gcc530/external/eigen/3.2.2/include")
            ROOT.gROOT.ProcessLine(".L %s/src/CMGTools/WMass/python/postprocessing/helpers/PDFWeightsHelper.cc+" % os.environ['CMSSW_BASE'])
        mc2hessianCSV = "%s/src/CMGTools/WMass/python/postprocessing/data/gen/NNPDF30_nlo_as_0118_hessian_60.csv" % os.environ['CMSSW_BASE']
        self._pdfHelper = ROOT.PDFWeightsHelper()
        self._pdfHelper.Init(self.nMCReplicasWeights,self.nHessianWeights,mc2hessianCSV)
    def beginJob(self):
        pass
    def endJob(self):
        pass
    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.initReaders(inputTree) # initReaders must be called in beginFile
        self.out = wrappedOutputTree
        self.out.branch("weightGen", "F")
        self.out.branch("partonId1", "I")
        self.out.branch("partonId2", "I")
        self.out.branch("nGenLepDressed", "I")
        self.out.branch("nGenPromptNu", "I")
        for V in self.vars:
            self.out.branch("GenLepDressed_"+V, "F", lenVar="nGenLepDressed")
            self.out.branch("GenPromptNu_"+V, "F", lenVar="nGenPromptNu")
        for V in self.genwvars:
            self.out.branch("genw_"+V, "F")
            self.out.branch("lhew_"+V, "F")
        self.out.branch("hessWgt", "F", n=self.nHessianWeights)
    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass

    def initReaders(self,tree): # this function gets the pointers to Value and ArrayReaders and sets them in the C++ worker class
        try:
            self.nGenPart = tree.valueReader("nGenPart")
            for B in ("pt","eta","phi","mass","pdgId","isPromptHard","motherId","status") : setattr(self,"GenPart_"+B, tree.arrayReader("GenPart_"+B))
            self._worker.setGenParticles(self.nGenPart,self.GenPart_pt,self.GenPart_eta,self.GenPart_phi,self.GenPart_mass,self.GenPart_pdgId,self.GenPart_isPromptHard,self.GenPart_motherId,self.GenPart_status)
            #self.nLHEweight = tree.valueReader("nLHEweight")
            #self.LHEweight_wgt = tree.arrayReader("LHEweight_wgt")
        except:
            print '[genFriendProducer][Warning] Unable to attach to generator-level particles (data only?). No info will be produced'
        self._ttreereaderversion = tree._ttreereaderversion # self._ttreereaderversion must be set AFTER all calls to tree.valueReader or tree.arrayReader

    def mcRep2Hess(self,weight,lheweights):
        nomlhew = lheweights[0]
        inPdfW = np.array(lheweights[self.pdfWeightOffset:self.pdfWeightOffset+self.nMCReplicasWeights],dtype=float)
        outPdfW = np.array([0 for i in xrange(self.nHessianWeights)],dtype=float)
        self._pdfHelper.DoMC2Hessian(nomlhew,inPdfW,outPdfW)
        pdfeigweights = [wgt*weight/nomlhew for wgt in outPdfW.tolist()]
        return pdfeigweights

    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""
        lhe_wgts = Collection(event,"LHEweight")
        if event._tree._ttreereaderversion > self._ttreereaderversion: # do this check at every event, as other modules might have read further branches
            self.initReaders(event._tree)

        # do NOT access other branches in python between the check/call to initReaders and the call to C++ worker code
        ## Algo
        self._worker.run()
        dressedLeptons = self._worker.dressedLeptons()
        neutrinos = self._worker.promptNeutrinos()
        lepPdgIds = self._worker.dressedLeptonsPdgId()
        nuPdgIds = self._worker.promptNeutrinosPdgId()
        lheWs    = self._worker.lheWs()
        lheWPdgIds = self._worker.lheWsPdgId()
        lheLeps    = self._worker.lheLeps()
        lheLepPdgIds = self._worker.lheLepsPdgId()

        #nothing to do if this is data
        if event.isData: return True

        if hasattr(event,"genWeight"):
            self.out.fillBranch("weightGen", getattr(event, "genWeight"))
            self.out.fillBranch("partonId1", getattr(event, "id1"))
            self.out.fillBranch("partonId2", getattr(event, "id2"))
        else:
            self.out.fillBranch("weightGen", -999.)
            self.out.fillBranch("partonId1", -999 )
            self.out.fillBranch("partonId2", -999 )
        retL={}
        retL["pt"] = [dl.Pt() for dl in dressedLeptons]
        retL["eta"] = [dl.Eta() for dl in dressedLeptons]
        retL["phi"] = [dl.Phi() for dl in dressedLeptons]
        retL["mass"] = [dl.M() for dl in dressedLeptons]
        retL["pdgId"] = [pdgId for pdgId in lepPdgIds]
        self.out.fillBranch("nGenLepDressed", len(dressedLeptons))
        for V in self.vars:
            self.out.fillBranch("GenLepDressed_"+V, retL[V])
        self.out.fillBranch("GenLepDressed_pdgId", [pdgId for pdgId in lepPdgIds])

        retN={}
        retN["pt"] = [nu.Pt() for nu in neutrinos]
        retN["eta"] = [nu.Eta() for nu in neutrinos]
        retN["phi"] = [nu.Phi() for nu in neutrinos]
        retN["mass"] = [nu.M() for nu in neutrinos]
        retN["pdgId"] = [pdgId for pdgId in lepPdgIds]
        self.out.fillBranch("nGenPromptNu", len(neutrinos))
        for V in self.vars:
            self.out.fillBranch("GenPromptNu_"+V, retN[V])
        self.out.fillBranch("GenPromptNu_pdgId", [pdgId for pdgId in nuPdgIds])

        if len(lheWs):
            if len(lheWs) > 1:
                print 'WARNING: MORE THAN 1 W BOSON FOUND. filling first in list'
            self.out.fillBranch("lhew_charge" , float(np.sign(lheWPdgIds[0])))
            self.out.fillBranch("lhew_pt"     , lheWs[0].Pt())
            self.out.fillBranch("lhew_eta"    , lheWs[0].Eta())
            self.out.fillBranch("lhew_phi"    , lheWs[0].Phi())
            self.out.fillBranch("lhew_y"      , lheWs[0].Rapidity())
            self.out.fillBranch("lhew_mass"   , lheWs[0].M())
            (lplus,lminus) = (neutrinos[0],lheLeps[0]) if lheLepPdgIds[0]<0 else (lheLeps[0],neutrinos[0])
            kv = KinematicVars()
            self.out.fillBranch("lhew_costcm" , kv.cosThetaCM(lplus,lminus))
            self.out.fillBranch("lhew_costcs" , kv.cosThetaCS(lplus,lminus))
            self.out.fillBranch("lhew_phics"  , kv.phiCS(lplus,lminus))
            self.out.fillBranch("lhew_mt"     , sqrt(2*lplus.Pt()*lminus.Pt()*(1.-cos(deltaPhi(lplus.Phi(),lminus.Phi())))))
            self.out.fillBranch("lhew_decayId", abs(nuPdgIds[0]))
        else:
            for V in self.genwvars:
                self.out.fillBranch("lhew_"+V, -999)

        if len(dressedLeptons) and len(neutrinos):
            genw = dressedLeptons[0] + neutrinos[0]
            self.out.fillBranch("genw_charge",float(-1*np.sign(lepPdgIds[0])))
            self.out.fillBranch("genw_pt",genw.Pt())
            self.out.fillBranch("genw_eta",genw.Eta())
            self.out.fillBranch("genw_phi",genw.Phi())
            self.out.fillBranch("genw_y",genw.Rapidity())
            self.out.fillBranch("genw_mass",genw.M())
            kv = KinematicVars(self.beamEn)
            # convention for phiCS: use l- direction for W-, use neutrino for W+
            (lplus,lminus) = (neutrinos[0],dressedLeptons[0]) if lepPdgIds[0]<0 else (dressedLeptons[0],neutrinos[0])
            self.out.fillBranch("genw_costcm",kv.cosThetaCM(lplus,lminus))
            self.out.fillBranch("genw_costcs",kv.cosThetaCS(lplus,lminus))
            self.out.fillBranch("genw_phics",kv.phiCS(lplus,lminus))
            self.out.fillBranch("genw_mt"   , sqrt(2*lplus.Pt()*lminus.Pt()*(1.-cos(deltaPhi(lplus.Phi(),lminus.Phi())) )))
            self.out.fillBranch("genw_decayId", abs(nuPdgIds[0]))
        else:
            ##if not len(dressedLeptons): 
            ##    print '================================'
            ##    print 'no dressed leptons found!'
            ##    print 'no dressed leptons fround :lumi:evt: {a}:{b}:{c}'.format(a=getattr(event, "run"),b=getattr(event, "lumi"),c=getattr(event, "evt"))
            ##else:
            ##    print '================================'
            ##    print 'no neutrinos found, in run:lumi:evt: {a}:{b}:{c}'.format(a=getattr(event, "run"),b=getattr(event, "lumi"),c=getattr(event, "evt"))
            for V in self.genwvars:
                self.out.fillBranch("genw_"+V, -999)

        lheweights = [w.wgt for w in lhe_wgts]
        hessWgt = self.mcRep2Hess(getattr(event, "genWeight"),lheweights)
        self.out.fillBranch("hessWgt",hessWgt)

        return True

# define modules using the syntax 'name = lambda : constructor' to avoid having them loaded when not needed

genQEDJets14TeV = lambda : GenQEDJetProducer(deltaR=0.1,beamEn=7000.)
genQEDJets = lambda : GenQEDJetProducer(deltaR=0.1,beamEn=6500.)

