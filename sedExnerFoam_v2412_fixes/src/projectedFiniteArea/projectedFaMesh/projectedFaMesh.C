/*---------------------------------------------------------------------------* \
Copyright (C) 2022 Matthias Renaud, Cyrille Bonamy, Julien Chauchat
                   and contributors

License
    This file is part of ScourFOAM.

    ScourFOAM is free software: you can redistribute it and/or modify it
    under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    ScourFOAM is distributed in the hope that it will be useful, but WITHOUT
    ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
    FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
    for more details.

    You should have received a copy of the GNU General Public License
    along with ScourFOAM.  If not, see <http://www.gnu.org/licenses/>.

\*---------------------------------------------------------------------------*/

#include "projectedFaMesh.H"

// * * * * * * * * * * * * * Private Member Functions  * * * * * * * * * * * //

void Foam::projectedFaMesh::clearGeom() const
{
    deleteDemandDrivenData(areaCentresPtr_);
    deleteDemandDrivenData(edgeCentresPtr_);
}

// * * * * * * * * * * * * * * * * Constructors  * * * * * * * * * * * * * * //

Foam::projectedFaMesh::projectedFaMesh
(
    const faMesh& aMesh,
    vector projectNormal
)
:
    mesh_(aMesh),
    nPoints_(aMesh.nPoints()),
    nEdges_(aMesh.nEdges()),
    nInternalEdges_(aMesh.nInternalEdges()),
    nFaces_(aMesh.nFaces()),
    edgeOwner_(aMesh.edgeOwner()),
    edgeNeighbour_(aMesh.edgeNeighbour()),
    projectNormal_(projectNormal/mag(projectNormal)),
    LePtr_(nullptr),
    magLePtr_(nullptr),
    areaCentresPtr_(nullptr),
    edgeCentresPtr_(nullptr),
    pointCoordsPtr_(nullptr),
    SPtr_(nullptr)
{}

// * * * * * * * * * * * * * * * * Destructor  * * * * * * * * * * * * * * * //

Foam::projectedFaMesh::~projectedFaMesh()
{
    clearGeom();
}

// * * * * * * * * * * * * * * * Member Functions  * * * * * * * * * * * * * //

const faMesh& Foam::projectedFaMesh::mesh() const
{
    return mesh_;
}

label Foam::projectedFaMesh::nPoints() const
{
    return nPoints_;
}

label Foam::projectedFaMesh::nEdges() const
{
    return nEdges_;
}

label Foam::projectedFaMesh::nInternalEdges() const
{
    return nInternalEdges_;
}

label Foam::projectedFaMesh::nFaces() const
{
    return nFaces_;
}

const labelList Foam::projectedFaMesh::edgeOwner() const
{
    return edgeOwner_;
}

const labelList Foam::projectedFaMesh::edgeNeighbour() const
{
    return edgeNeighbour_;
}

const vectorField& Foam::projectedFaMesh::Le() const
{
    if (LePtr_==nullptr)
    {
        calcLe();
    }

    return *LePtr_;
}

const scalarField& Foam::projectedFaMesh::magLe() const
{
    if (magLePtr_==nullptr)
    {
        calcMagLe();
    }

    return *magLePtr_;
}

const vectorField& Foam::projectedFaMesh::areaCentres() const
{
    if (areaCentresPtr_==nullptr)
    {
        calcAreaCentres();
    }

    return *areaCentresPtr_;
}

const vectorField& Foam::projectedFaMesh::edgeCentres() const
{
    if (edgeCentresPtr_==nullptr)
    {
        calcEdgeCentres();
    }

    return *edgeCentresPtr_;
}

const vectorField& Foam::projectedFaMesh::pointCoords() const
{
    if (pointCoordsPtr_==nullptr)
    {
        calcPointCoords();
    }

    return *pointCoordsPtr_;
}


const scalarField& Foam::projectedFaMesh::S() const
{
    if (SPtr_==nullptr)
    {
        calcS();
    }

    return *SPtr_;
}

vectorField Foam::projectedFaMesh::project
(
    vectorField field
) const
{
    return field - (field & projectNormal_) * projectNormal_;
}

vector Foam::projectedFaMesh::project
(
    vector vec
) const
{
    return vec - (vec & projectNormal_) * projectNormal_;
}

// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //
