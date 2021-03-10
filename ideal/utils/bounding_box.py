# -----------------------------------------------------------------------------
#   Copyright (C): MedAustron GmbH, ACMIT Gmbh and Medical University Vienna
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE for further details
# -----------------------------------------------------------------------------

import numpy as np

class bounding_box(object):
    """
    Define ranges in which things are in 3D space.
    Maybe this should be more dimensionally flexible, to also handle 2D or N
    dimensional bounding boxes.
    """
    def __init__(self,**kwargs):
        """
        Initialize using *one* of the following kwargs:
        * 'bb': copy from another bounding_box object
        * 'img': obtain bounding box from a 'itk' image
        * 'xyz': initialize bounding box with 6 floats, shaped (x1,y1,z1,x2,y2,z2),
          ((x1,x2),(y1,y2),(z1,z2)) or ((x1,y1,z1),(x2,y2,z2)).
        TODO: maybe 'extent' would be a better name for the "limits" data member.
        TODO: maybe the different kind of constructors should be implemented as static methods instead of with kwargs.
        """
        nkeys = len(kwargs.keys())
        self.limits=np.empty((3,2))
        if nkeys == 0:
            self.reset()
        elif nkeys > 1:
            raise RuntimeError("too many arguments ({}) to bounding box constructor: {}".format(nkeys,kwargs))
        elif "bb" in kwargs:
            bb = kwargs["bb"]
            self.limits = np.copy(bb.limits)
        elif "img" in kwargs:
            img = kwargs["img"]
            if len(img.GetOrigin()) != 3:
                raise ValueError("only 3D bounding boxes/images are supported")
            origin = np.array(img.GetOrigin())
            spacing = np.array(img.GetSpacing())
            dims = np.array(img.GetLargestPossibleRegion().GetSize())
            self.limits[:,0] = origin-0.5*spacing
            self.limits[:,1] = origin+(dims-0.5)*spacing
        elif "xyz" in kwargs:
            xyz = np.array(kwargs["xyz"],dtype=float)
            if xyz.shape==(3,2):
                self.limits = xyz
            elif xyz.shape==(2,3):
                self.limits = xyz.T
            elif xyz.shape==(6,):
                self.limits = xyz.reshape(3,2)
            else:
                raise ValueError("unsupported shape for xyz limits: {}".format(xyz.shape))
            if np.logical_not(self.limits[:,0]<=self.limits[:,1]).any():
                raise ValueError("min should be less or equal max but I got min={} max={}".format(self.limits[:,0],self.limits[:,1]))
    def reset(self):
        self.limits[:,0]=np.inf
        self.limits[:,1]=-np.inf
    def __repr__(self):
        return "bounding box [[{},{}],[{},{}],[{},{}]]".format(*(self.limits.flat[:].tolist()))
    @property
    def volume(self):
        if np.isinf(self.limits).any():
            return 0.
        return np.prod(np.diff(self.limits,axis=1))
    @property
    def empty(self):
        return (self.volume == 0.)
    def __eq__(self,rhs):
        if self.empty and rhs.empty:
            return True
        return (self.limits==rhs.limits).all()
    def should_contain(self,point):
        apoint = np.array(point,dtype=float)
        assert(len(apoint.shape)==1)
        assert(apoint.shape[0]==3)
        self.limits[:,0] = np.min([self.limits[:,0],apoint],axis=0)
        self.limits[:,1] = np.max([self.limits[:,1],apoint],axis=0)
    def should_contain_all(self,points):
        assert(np.array(points).shape[1]==3)
        self.should_contain(np.min(points,axis=0))
        self.should_contain(np.max(points,axis=0))
    @property
    def mincorner(self):
        return self.limits[:,0]
    @property
    def maxcorner(self):
        return self.limits[:,1]
    @property
    def center(self):
        return 0.5*(self.mincorner+self.maxcorner)
    def contains(self,point,inner=False,rtol=0.,atol=1e-3):
        assert(len(point)==3)
        apoint=np.array(point)
        if inner:
            # really inside, NOT at the boundary (within rounding errors)
            gt_lo_lim = np.logical_not(np.isclose(self.limits[:,0],apoint,rtol=rtol,atol=atol))*(apoint>self.limits[:,0])
            lt_up_lim = np.logical_not(np.isclose(self.limits[:,1],apoint,rtol=rtol,atol=atol))*(apoint<self.limits[:,1])
            return (gt_lo_lim*lt_up_lim).all()
        else:
            # inside, or at the boundary (within rounding errors)
            ge_lo_lim = np.isclose(self.limits[:,0],apoint,rtol=rtol,atol=atol)|(apoint>self.limits[:,0])
            le_up_lim = np.isclose(self.limits[:,1],apoint,rtol=rtol,atol=atol)|(apoint<self.limits[:,1])
            return (ge_lo_lim*le_up_lim).all()
    def encloses(self,bb,inner=False,rtol=0.,atol=1e-3):
        return (self.contains(bb.mincorner,inner) and self.contains(bb.maxcorner,inner))
    def __contains__(self,item):
        """
        Support for the 'in' operator

        Works only for other bounding boxes, and for 3D points represented by numpy arrays of shape (3,).
        """
        if type(item)==type(self):
            return self.encloses(item)
        else:
            return self.contains(item)
    def add_margins(self,margins):
        # works both with scalar and vector
        # TODO: allow negative margins, but implement appropriate behavior in case margin is larger than the bb.
        self.limits[:,0]-=margins
        self.limits[:,1]+=margins
    def merge(self,bb):
        if self.empty:
            self.limits = np.copy(bb.limits)
        elif not bb.empty:
            self.should_contain(bb.mincorner)
            self.should_contain(bb.maxcorner)
    def have_overlap(self,bb):
        # not sure this is correct!
        return ((not self.empty) and (not bb.empty) and (self.limits[:,0]<=bb.limits[:,1]).all() and (bb.limits[:,0]<=self.limits[:,1]).all())
    def intersect(self,bb):
        if not self.have_overlap(bb):
            self.reset()
        else:
            self.limits[:,0] = np.max([self.mincorner,bb.mincorner],axis=0)
            self.limits[:,1] = np.min([self.maxcorner,bb.maxcorner],axis=0)
    def indices_in_image(self,img,rtol=0.,atol=1e-3):
        """
        Determine the voxel indices of the bounding box corners in a given image.

        In case the corners are within rounding margin (given by `eps`) on a
        boundary between voxels in the image, then voxels that would only have
        an infinitesimal intersection with the bounding box are not included.
        The parameters `atol` and `rtol` are used to determine with
        `np.isclose` if BB corners are on a voxel boundary. In case the BB
        corners are outside of the image volume, the indices will be out of the
        range (negative, of larger than image size).

        Returns two numpy arrays of size 3 and dtype int, representing the
        inclusive/exclusive image indices of the lower/upper corners,
        respectively.
        """
        # generically, this is what we want to do:
        bb_img = bounding_box(img=img)
        spacing = np.array(img.GetSpacing())
        ibbmin,devmin=np.divmod(self.mincorner-bb_img.mincorner,spacing)
        ibbmax,devmax=np.divmod(self.maxcorner-bb_img.mincorner,spacing)
        # but if we are "almost exactly" on a voxel boundary we need to be picky on which side to land
        below=np.isclose(devmin,spacing,rtol=rtol,atol=atol)
        above=(devmax>atol)
        ibbmin[below]+=1 # add one IF on a voxel boundary
        ibbmax[above]+=1 # add one UNLESS on a voxel boundary
        return np.int32(ibbmin),np.int32(ibbmax)
    @property
    def xmin(self):
        return self.limits[0,0]
    @property
    def xmax(self):
        return self.limits[0,1]
    @property
    def ymin(self):
        return self.limits[1,0]
    @property
    def ymax(self):
        return self.limits[1,1]
    @property
    def zmin(self):
        return self.limits[2,0]
    @property
    def zmax(self):
        return self.limits[2,1]

#######################################################################
# TESTING
#######################################################################
import unittest

class test_bounding_box(unittest.TestCase):
    def test_xyz_constructor(self):
        bb0 = bounding_box(xyz=[[1,2],[3,4],[5,6]])
        self.assertTrue( ( bb0.limits.flat == np.arange(1,7) ).all() )
        bb1 = bounding_box(xyz=[[1,3,5],[2,4,6]])
        self.assertTrue( ( bb1.limits.flat == np.arange(1,7) ).all() )
        bb2 = bounding_box(xyz=[1,2,3,4,5,6])
        self.assertTrue( ( bb2.limits.flat == np.arange(1,7) ).all() )
        bb3 = bounding_box(xyz=range(1,7))
        self.assertTrue( ( bb3.limits.flat == np.arange(1,7) ).all() )
        with self.assertRaises(ValueError):
            bbxyz_wrong = bounding_box(xyz=[[1,2],[4,3],[5,6]])
        with self.assertRaises(ValueError):
            bbxyz_wrong = bounding_box(xyz=[[np.nan,2],[4,3],[5,6]])
        with self.assertRaises(ValueError):
            bbxyz_wrong = bounding_box(xyz=[[1,2],[3],[5,6,7]])
        with self.assertRaises(ValueError):
            bbxyz_wrong = bounding_box(xyz=[[1,2],[3],[5,6]])
        with self.assertRaises(ValueError):
            bbxyz_wrong = bounding_box(xyz=[1,2,3,4,5,6,7])
        with self.assertRaises(ValueError):
            bbxyz_wrong = bounding_box(xyz=[1,2,3,4,5])
    def test_max_one_key_constructor(self):
        with self.assertRaises(RuntimeError):
            bb0 = bounding_box()
            bbxyz = bounding_box(xyz=[[1,2],[3,4],[5,6]],bb=bb0)
    def test_bb_constructor(self):
        bbxyz = bounding_box(xyz=[[1,2],[3,4],[5,6]])
        bbxyz2 = bounding_box(bb=bbxyz)
        self.assertTrue( (bbxyz.limits == bbxyz2.limits).all() )
        self.assertFalse( bbxyz.limits is bbxyz2.limits ) # it should be a *copy*, not a reference to the same object
    def test_default_constructor(self):
        bb0 = bounding_box()
        self.assertTrue( np.isinf(bb0.limits).all() )
        self.assertTrue( (bb0.limits[:,0]>0).all() )
        self.assertTrue( (bb0.limits[:,1]<0).all() )
    def test_equal(self):
        bb0 = bounding_box(xyz=[[1,2],[3,4],[5,6]])
        bb1 = bounding_box(xyz=[[1,2],[3,4],[5,6]]) # same
        bb2 = bounding_box(xyz=[[1,2],[3,5],[5,6]]) # different
        self.assertTrue(bb0==bb1)
        self.assertFalse(bb0==bb2)
        bb0 = bounding_box()
        bb1 = bounding_box()
        self.assertTrue(bb0==bb1) # empty is empty
        self.assertFalse(bb0==bb2) # empty is not full
        bb0 = bounding_box()
        bb1 = bounding_box(bb=bb0)
        self.assertTrue(bb0==bb1)
        self.assertFalse(bb1==bb2)
        bb1 = bounding_box(xyz=[[1,2],[3,4],[5,5]])
        self.assertTrue(bb0==bb1) # both bounding boxes are empty
        self.assertFalse(bb1==bb2)
    def test_corners(self):
        bbxyz = bounding_box(xyz=[[1,2],[3,4],[5,6]])
        self.assertTrue((bbxyz.mincorner == np.array([1.,3.,5.])).all())
        self.assertTrue((bbxyz.maxcorner == np.array([2.,4.,6.])).all())
    def test_contains(self):
        bbxyz = bounding_box(xyz=[[1,2],[3,4],[5,6]])
        xx,yy,zz = np.meshgrid(np.arange(0.5,2.6,1.0), np.arange(2.5,4.6,1.0), np.arange(4.5,6.6,1.0) )
        for i,point in enumerate(zip(xx.flat,yy.flat,zz.flat)):
            if i==13:
                self.assertTrue(bbxyz.contains(point))
            else:
                self.assertFalse(bbxyz.contains(point))
        self.assertTrue(bbxyz.contains(bbxyz.mincorner,inner=False))
        self.assertFalse(bbxyz.contains(bbxyz.mincorner,inner=True))
        self.assertTrue(bbxyz.contains(bbxyz.maxcorner,inner=False))
        self.assertFalse(bbxyz.contains(bbxyz.maxcorner,inner=True))
        atol=1e-4
        for rounding_error in [ -1.3*atol,-0.5*atol,+0.5*atol,1.5*atol]:
            if np.abs(rounding_error)<atol:
                # on the boundary != inside
                self.assertTrue(bbxyz.contains(bbxyz.mincorner+rounding_error,inner=False,atol=atol))
                self.assertTrue(bbxyz.contains(bbxyz.maxcorner+rounding_error,inner=False,atol=atol))
                self.assertFalse(bbxyz.contains(bbxyz.mincorner+rounding_error,inner=True,atol=atol))
                self.assertFalse(bbxyz.contains(bbxyz.maxcorner+rounding_error,inner=True,atol=atol))
            elif rounding_error<-atol:
                # not on the boundary: same verdict regardless of 'inner' setting
                self.assertFalse(bbxyz.contains(bbxyz.mincorner+rounding_error,inner=False,atol=atol))
                self.assertFalse(bbxyz.contains(bbxyz.mincorner+rounding_error,inner=True,atol=atol))
                self.assertTrue(bbxyz.contains(bbxyz.maxcorner+rounding_error,inner=False,atol=atol))
                self.assertTrue(bbxyz.contains(bbxyz.maxcorner+rounding_error,inner=True,atol=atol))
            elif rounding_error>+atol:
                # not on the boundary: same verdict regardless of 'inner' setting
                self.assertTrue(bbxyz.contains(bbxyz.mincorner+rounding_error,inner=False,atol=atol))
                self.assertTrue(bbxyz.contains(bbxyz.mincorner+rounding_error,inner=True,atol=atol))
                self.assertFalse(bbxyz.contains(bbxyz.maxcorner+rounding_error,inner=False,atol=atol))
                self.assertFalse(bbxyz.contains(bbxyz.maxcorner+rounding_error,inner=True,atol=atol))
    def test_grow(self):
        bbxyz = bounding_box(xyz=[[1,2],[3,4],[5,6]])
        for point in np.array(range(30)).reshape(10,3):
            bbxyz.should_contain(point)
            self.assertTrue(bbxyz.contains(point,inner=False))
        self.assertFalse(bbxyz.contains((0,0,0)))
        self.assertFalse(bbxyz.contains((0,0,30)))
        self.assertFalse(bbxyz.contains((-1,10,10)))
        bbxyz2 = bounding_box(xyz=[[1,2],[3,4],[5,6]])
        bbxyz2.should_contain_all( np.array(range(30)).reshape(10,3) )
        self.assertEqual(bbxyz,bbxyz2)
    def test_grow_margin(self):
        # scalar grow ##################################################
        bbxyz = bounding_box(xyz=[1,2,3,4,5,6])
        bbxyz.add_margins(0.5)
        self.assertTrue( (bbxyz.limits.flat == np.array([0.5,2.5,2.5,4.5,4.5,6.5])).all() )
        # scalar shrink ################################################
        bbxyz = bounding_box(xyz=[1,2,3,4,5,6])
        bbxyz.add_margins(-0.25)
        self.assertTrue( (bbxyz.limits.flat == np.array([1.25,1.75,3.25,3.75,5.25,5.75])).all() )
        # vector grow ##################################################
        bbxyz = bounding_box(xyz=[1,2,3,4,5,6])
        bbxyz.add_margins(np.array([1,3,5]))
        self.assertTrue( (bbxyz.limits[:,0] == 0.).all() )
        bbxyz = bounding_box(xyz=[1,2,3,4,5,6])
        bbxyz.add_margins(np.array([8,6,4]))
        self.assertTrue( (bbxyz.limits[:,1] == 10.).all() )
    def test_merge(self):
        bbxyz0 = bounding_box(xyz=np.arange(1,7))
        bbxyz1 = bounding_box(xyz=np.array([1.1,1.9,3.1,3.9,5.1,5.9]))
        bbxyz2 = bounding_box(xyz=np.arange(1.1,7,1.1))
        bbxyz0.merge(bbxyz1) # should not change anything
        self.assertTrue( (bbxyz0.limits[:,0] == np.arange(1,7,2)).all() )
        bbxyz0.merge(bbxyz2)
        self.assertTrue( (bbxyz0.limits[:,0] == np.arange(1,5.1,2)).all() ) # lower limits unchanged
        self.assertTrue( (bbxyz0.limits[:,1] == np.arange(1.1,7,1.1)[1::2]).all() ) # upper limits changed
    def test_intersect(self):
        bbxyz0 = bounding_box(xyz=np.arange(1,7))
        bbxyz1 = bounding_box(xyz=np.arange(1,7)+0.5)
        bbxyz0.intersect(bbxyz1)
        self.assertTrue( (bbxyz0.limits[:,0] == np.arange(1.5,5.6,2)).all() ) # lower limits changed
        self.assertTrue( (bbxyz0.limits[:,1] == np.arange(2,7,2)).all() ) # upper limits unchanged
    def test_indices_in_image(self):
        import itk
        image = itk.image_from_array(np.ones((7,6,5),dtype=np.int16))
        image.SetOrigin((0.75,0.65,0.55))
        image.SetSpacing((1.5,1.3,1.1))
        # single voxel box
        single_voxel_box = bounding_box(xyz=[[0.05,0.05,0.05],[1.45,1.25,1.05]])
        imin,imax=single_voxel_box.indices_in_image(image)
        self.assertTrue( (imin==np.zeros(3)).all() )
        self.assertTrue( (imax==np.ones(3)).all() )
        # image box
        img_box = bounding_box(img=image)
        imin,imax=img_box.indices_in_image(image)
        self.assertTrue( issubclass(imin.dtype.type,np.integer) )
        self.assertTrue( issubclass(imax.dtype.type,np.integer) )
        self.assertTrue( (imin==np.zeros(3)).all() )
        self.assertTrue( (imax==np.array(image.GetLargestPossibleRegion().GetSize())).all() )
        # image box with rounding errors
        atol = 1e-4
        for i in range(10):
            # within tolerance
            img_boxy = bounding_box(xyz=img_box.limits+np.random.uniform(-atol,+atol,img_box.limits.shape))
            imin,imax=img_boxy.indices_in_image(image,atol=atol)
            self.assertTrue( (imin==np.zeros(3)).all() )
            self.assertTrue( (imax==np.array(image.GetLargestPossibleRegion().GetSize())).all() )
            # a bit more than the tolerance in one direction
            img_boks = bounding_box(xyz=img_box.limits+np.random.uniform(+atol,+2.0*atol,img_box.limits.shape))
            imin,imax=img_boks.indices_in_image(image,atol=atol)
            self.assertTrue( (imin==np.zeros(3)).all() )
            self.assertTrue( (imax-1==np.array(image.GetLargestPossibleRegion().GetSize())).all() )
            # a bit more than the tolerance in the other direction
            img_bokz = bounding_box(xyz=img_box.limits-np.random.uniform(+atol,+2.0*atol,img_box.limits.shape))
            imin,imax=img_bokz.indices_in_image(image,atol=atol)
            self.assertTrue( (imin+1==np.zeros(3)).all() )
            self.assertTrue( (imax==np.array(image.GetLargestPossibleRegion().GetSize())).all() )
        # box partly outside of image, x coordinates exacly on a voxel boundary
        side_box = bounding_box(xyz=[[-3.,-3.,2.],[6.,6.,6.]])
        imin,imax=side_box.indices_in_image(image,atol=atol)
        self.assertTrue( (imin==np.array([-2,-3, 1])).all())
        self.assertTrue( (imax==np.array([ 4, 5, 6])).all())

# vim: set et softtabstop=4 sw=4 smartindent:
