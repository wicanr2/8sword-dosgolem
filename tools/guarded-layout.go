//go:build ignore

// Fixed PAM: 42 guards, source serializer mapping and actual terrain markers.
package main

const guardedSaveBase = 1508
const guardedCodeSHA = "a51411880047cfccb77fb24e9164710681c717be6f7a9abcd04d56cb5fe1f1ce"

var guardedBases = [8]uint16{0x365e, 0x3706, 0x3766, 0x37c6, 0x3826, 0x3886, 0x38e6, 0x3946}
var guardedCoordinates = [8][][2]uint16{
	{{5, 4}, {48, 5}, {19, 29}, {63, 42}, {58, 52}, {57, 70}, {9, 73}},
	{{7, 13}, {5, 48}, {43, 54}, {27, 69}},
	{{29, 14}, {54, 28}, {6, 30}, {29, 77}},
	{{41, 22}, {62, 34}, {8, 37}, {32, 62}},
	{{12, 37}, {48, 37}, {53, 54}, {22, 61}},
	{{63, 12}, {9, 25}, {14, 44}, {35, 72}},
	{{27, 13}, {64, 38}, {18, 58}, {41, 74}},
	{{57, 5}, {12, 8}, {38, 12}, {23, 15}, {10, 38}, {19, 38}, {57, 42}, {26, 51}, {11, 59}, {29, 75}, {61, 76}},
}
